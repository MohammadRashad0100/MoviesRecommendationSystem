import os
import time
import pickle
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any, Tuple

import numpy as np
import pandas as pd
import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# =========================
# ENV
# =========================
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG_500 = "https://image.tmdb.org/t/p/w500"
TMDB_IMG_ORIGINAL = "https://image.tmdb.org/t/p/original"

if not TMDB_API_KEY:
    raise RuntimeError("TMDB_API_KEY missing. Put it in .env as TMDB_API_KEY=xxxx")

# =========================
# SIMPLE IN-MEMORY TMDB CACHE
# =========================
_TMDB_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_TMDB_CACHE_TTL = 120  # seconds
_TMDB_CACHE_MAX_ENTRIES = 1000

# =========================
# PICKLE GLOBALS
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DF_PATH           = os.path.join(BASE_DIR, "df.pkl")
INDICES_PATH      = os.path.join(BASE_DIR, "indices.pkl")
TFIDF_MATRIX_PATH = os.path.join(BASE_DIR, "tfidf_matrix.pkl")
TFIDF_PATH        = os.path.join(BASE_DIR, "tfidf.pkl")

df: Optional[pd.DataFrame] = None
indices_obj: Any = None
tfidf_matrix: Any = None
tfidf_obj: Any = None
TITLE_TO_IDX: Optional[Dict[str, int]] = None

# =========================
# LIFESPAN
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    global df, indices_obj, tfidf_matrix, tfidf_obj, TITLE_TO_IDX

    for path, label in [
        (DF_PATH, "df.pkl"),
        (INDICES_PATH, "indices.pkl"),
        (TFIDF_MATRIX_PATH, "tfidf_matrix.pkl"),
        (TFIDF_PATH, "tfidf.pkl"),
    ]:
        if not os.path.exists(path):
            raise RuntimeError(f"Required file not found: {path} ({label})")

    with open(DF_PATH, "rb") as f:
        df = pickle.load(f)
    with open(INDICES_PATH, "rb") as f:
        indices_obj = pickle.load(f)
    with open(TFIDF_MATRIX_PATH, "rb") as f:
        tfidf_matrix = pickle.load(f)
    with open(TFIDF_PATH, "rb") as f:
        tfidf_obj = pickle.load(f)

    if not isinstance(df, pd.DataFrame) or "title" not in df.columns:
        raise RuntimeError("df.pkl must be a DataFrame with a 'title' column")

    TITLE_TO_IDX = build_title_to_idx_map(indices_obj)
    yield

# =========================
# FASTAPI APP
# =========================
app = FastAPI(title="Movie Recommender API", version="4.1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# MODELS
# =========================
class TMDBMovieCard(BaseModel):
    tmdb_id: int
    title: str
    poster_url: Optional[str] = None
    release_date: Optional[str] = None
    vote_average: Optional[float] = None

class TMDBMovieDetails(BaseModel):
    tmdb_id: int
    title: str
    overview: Optional[str] = None
    tagline: Optional[str] = None
    release_date: Optional[str] = None
    runtime: Optional[int] = None
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    genres: List[dict] = []
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    original_language: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[int] = None
    revenue: Optional[int] = None
    certification: Optional[str] = None  

class CastMember(BaseModel):
    cast_id: int
    name: str
    character: Optional[str] = None
    profile_url: Optional[str] = None
    order: int = 0

class VideoItem(BaseModel):
    key: str
    name: str
    site: str
    video_type: str
    official: bool = False

class TFIDFRecItem(BaseModel):
    title: str
    score: float
    tmdb: Optional[TMDBMovieCard] = None

class SearchBundleResponse(BaseModel):
    query: str
    movie_details: TMDBMovieDetails
    tfidf_recommendations: List[TFIDFRecItem]
    genre_recommendations: List[TMDBMovieCard]

class SimilarBundleResponse(BaseModel):
    tfidf_recommendations: List[TFIDFRecItem]
    genre_recommendations: List[TMDBMovieCard]

class HomePageResponse(BaseModel):
    movies: List[TMDBMovieCard]
    total_pages: int
    current_page: int

# =========================
# UTILS
# =========================
def _norm_title(t: str) -> str:
    return str(t).strip().lower()

def make_img_url(path: Optional[str], size: str = "w500") -> Optional[str]:
    if not path:
        return None
    return f"https://image.tmdb.org/t/p/{size}{path}"

async def tmdb_get(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    q = dict(params)
    q["api_key"] = TMDB_API_KEY

    cache_key = path + "?" + "&".join(
        f"{k}={v}" for k, v in sorted(q.items()) if k != "api_key"
    )
    now = time.time()
    cached = _TMDB_CACHE.get(cache_key)
    if cached and (now - cached[0]) < _TMDB_CACHE_TTL:
        return cached[1]

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(f"{TMDB_BASE}{path}", params=q)
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"TMDB request error: {type(e).__name__} | {repr(e)}")

    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"TMDB error {r.status_code}: {r.text[:300]}")

    data = r.json()
    if len(_TMDB_CACHE) > _TMDB_CACHE_MAX_ENTRIES:
        _TMDB_CACHE.clear()
    _TMDB_CACHE[cache_key] = (now, data)
    return data

async def tmdb_cards_from_results(results: List[dict], limit: int = 20) -> List[TMDBMovieCard]:
    out: List[TMDBMovieCard] = []
    for m in (results or [])[:limit]:
        tmdb_id_raw = m.get("id")
        if tmdb_id_raw is None:
            continue
        out.append(TMDBMovieCard(
            tmdb_id=int(tmdb_id_raw),
            title=m.get("title") or m.get("name") or "",
            poster_url=make_img_url(m.get("poster_path")),
            release_date=m.get("release_date"),
            vote_average=m.get("vote_average"),
        ))
    return out

async def tmdb_certification(tmdb_id: int) -> Optional[str]:
    try:
        data = await tmdb_get(f"/movie/{tmdb_id}/release_dates", {})
    except HTTPException:
        return None

    results = data.get("results") or []
    fallback: Optional[str] = None
    for entry in results:
        for rd in entry.get("release_dates", []):
            cert = (rd.get("certification") or "").strip()
            if not cert:
                continue
            if entry.get("iso_3166_1") == "US":
                return cert
            if fallback is None:
                fallback = cert
    return fallback

async def tmdb_movie_details(movie_id: int) -> TMDBMovieDetails:
    data, certification = await asyncio.gather(
        tmdb_get(f"/movie/{movie_id}", {"language": "en-US"}),
        tmdb_certification(movie_id),
    )
    raw_id = data.get("id")
    if raw_id is None:
        raise HTTPException(status_code=502, detail="TMDB returned movie with no id")
    return TMDBMovieDetails(
        tmdb_id=int(raw_id),
        title=data.get("title") or "",
        overview=data.get("overview"),
        tagline=data.get("tagline"),
        release_date=data.get("release_date"),
        runtime=data.get("runtime"),
        poster_url=make_img_url(data.get("poster_path")),
        backdrop_url=make_img_url(data.get("backdrop_path"), size="original"),
        genres=data.get("genres") or [],
        vote_average=data.get("vote_average"),
        vote_count=data.get("vote_count"),
        original_language=data.get("original_language"),
        status=data.get("status"),
        budget=data.get("budget"),
        revenue=data.get("revenue"),
        certification=certification,
    )

async def tmdb_search_movies(query: str, page: int = 1) -> Dict[str, Any]:
    return await tmdb_get("/search/movie", {
        "query": query,
        "include_adult": "false",
        "language": "en-US",
        "page": page,
    })

async def tmdb_search_first(query: str) -> Optional[dict]:
    try:
        data = await tmdb_search_movies(query=query, page=1)
        results = data.get("results") or []
        return results[0] if results else None
    except HTTPException:
        return None

# =========================
# TF-IDF HELPERS
# =========================
def build_title_to_idx_map(indices: Any) -> Dict[str, int]:
    title_to_idx: Dict[str, int] = {}
    try:
        for k, v in indices.items():
            title_to_idx[_norm_title(k)] = int(v)
    except Exception as e:
        raise RuntimeError(f"indices.pkl must be dict or pandas Series-like. Got: {e}")
    return title_to_idx

def get_local_idx_by_title(title: str) -> int:
    global TITLE_TO_IDX
    if TITLE_TO_IDX is None:
        raise HTTPException(status_code=500, detail="TF-IDF index map not initialized")
    idx = TITLE_TO_IDX.get(_norm_title(title))
    if idx is not None:
        return idx
    raise HTTPException(status_code=404, detail=f"Title not found in local dataset: '{title}'")

def tfidf_recommend_titles(query_title: str, top_n: int = 10) -> List[Tuple[str, float]]:
    global df, tfidf_matrix
    if df is None or tfidf_matrix is None:
        raise HTTPException(status_code=500, detail="TF-IDF resources not loaded")
    idx = get_local_idx_by_title(query_title)
    qv = tfidf_matrix[idx]
    if hasattr(qv, "toarray"):
        scores = (tfidf_matrix @ qv.T).toarray().ravel()
    else:
        scores = tfidf_matrix @ qv.ravel()

    order = np.argsort(-scores)
    out: List[Tuple[str, float]] = []
    for i in order:
        if int(i) == int(idx):
            continue
        try:
            title_i = str(df.iloc[int(i)]["title"])
        except (IndexError, KeyError):
            continue
        out.append((title_i, float(scores[int(i)])))
        if len(out) >= top_n:
            break
    return out

async def attach_tmdb_card_by_title(title: str) -> Optional[TMDBMovieCard]:
    try:
        m = await tmdb_search_first(title)
        if not m:
            return None
        raw_id = m.get("id")
        if raw_id is None:
            return None
        return TMDBMovieCard(
            tmdb_id=int(raw_id),
            title=m.get("title") or title,
            poster_url=make_img_url(m.get("poster_path")),
            release_date=m.get("release_date"),
            vote_average=m.get("vote_average"),
        )
    except Exception:
        return None

async def _build_similar_bundle(
    tmdb_id: int,
    details: TMDBMovieDetails,
    tfidf_top_n: int,
    genre_limit: int,
) -> SimilarBundleResponse:
    recs: List[Tuple[str, float]] = []
    try:
        recs = tfidf_recommend_titles(details.title, top_n=tfidf_top_n)
    except HTTPException:
        recs = []

    async def _enrich(title: str, score: float) -> TFIDFRecItem:
        card = await attach_tmdb_card_by_title(title)
        return TFIDFRecItem(title=title, score=score, tmdb=card)

    tfidf_items: List[TFIDFRecItem] = (
        list(await asyncio.gather(*[_enrich(t, s) for t, s in recs])) if recs else []
    )

    genre_recs: List[TMDBMovieCard] = []
    if details.genres:
        genre_id = details.genres[0]["id"]
        discover = await tmdb_get("/discover/movie", {
            "with_genres": genre_id,
            "language": "en-US",
            "sort_by": "popularity.desc",
            "page": 1,
        })
        cards = await tmdb_cards_from_results(discover.get("results") or [], limit=genre_limit + 1)
        genre_recs = [c for c in cards if c.tmdb_id != tmdb_id][:genre_limit]

    return SimilarBundleResponse(
        tfidf_recommendations=tfidf_items,
        genre_recommendations=genre_recs,
    )

# =========================
# ROUTES
# =========================
@app.get("/health")
def health():
    return {
        "status": "ok",
        "pickles_loaded": df is not None,
        "movie_count": len(df) if df is not None else 0,
        "tmdb_cache_entries": len(_TMDB_CACHE),
    }

@app.get("/home", response_model=HomePageResponse)
async def home(
    category: str = Query("trending"),
    page: int = Query(1, ge=1, le=10),
    limit: int = Query(24, ge=1, le=50),
):
    valid_categories = {"popular", "top_rated", "upcoming", "now_playing"}
    try:
        if category == "trending":
            data = await tmdb_get("/trending/movie/day", {"language": "en-US", "page": page})
        elif category in valid_categories:
            data = await tmdb_get(f"/movie/{category}", {"language": "en-US", "page": page})
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category '{category}'. Choose from: trending, {', '.join(sorted(valid_categories))}",
            )
        movies = await tmdb_cards_from_results(data.get("results") or [], limit=limit)
        return HomePageResponse(
            movies=movies,
            total_pages=min(int(data.get("total_pages", 1)), 10),
            current_page=page,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Home route failed: {e}")

@app.get("/home/genre", response_model=HomePageResponse)
async def home_by_genre(
    genre_id: int = Query(..., gt=0),
    page: int = Query(1, ge=1, le=10),
    limit: int = Query(24, ge=1, le=50),
    sort_by: str = Query("popularity.desc"),
):
    data = await tmdb_get("/discover/movie", {
        "with_genres": genre_id,
        "language": "en-US",
        "sort_by": sort_by,
        "page": page,
    })
    movies = await tmdb_cards_from_results(data.get("results") or [], limit=limit)
    return HomePageResponse(
        movies=movies,
        total_pages=min(int(data.get("total_pages", 1)), 10),
        current_page=page,
    )

@app.get("/genres")
async def get_genres():
    data = await tmdb_get("/genre/movie/list", {"language": "en-US"})
    return data.get("genres", [])

@app.get("/tmdb/search")
async def tmdb_search(
    query: str = Query(..., min_length=1),
    page: int = Query(1, ge=1, le=10),
):
    return await tmdb_search_movies(query=query, page=page)

@app.get("/movie/id/{tmdb_id}", response_model=TMDBMovieDetails)
async def movie_details_route(tmdb_id: int):
    if tmdb_id <= 0:
        raise HTTPException(status_code=400, detail="tmdb_id must be a positive integer")
    return await tmdb_movie_details(tmdb_id)

@app.get("/movie/id/{tmdb_id}/cast", response_model=List[CastMember])
async def movie_cast(
    tmdb_id: int,
    limit: int = Query(10, ge=1, le=30),
):
    if tmdb_id <= 0:
        raise HTTPException(status_code=400, detail="tmdb_id must be a positive integer")
    data = await tmdb_get(f"/movie/{tmdb_id}/credits", {"language": "en-US"})
    cast = data.get("cast") or []
    result: List[CastMember] = []
    for member in cast[:limit]:
        result.append(CastMember(
            cast_id=member.get("id", 0),
            name=member.get("name") or "",
            character=member.get("character"),
            profile_url=make_img_url(member.get("profile_path")),
            order=member.get("order", 0),
        ))
    return result

@app.get("/movie/id/{tmdb_id}/videos", response_model=List[VideoItem])
async def movie_videos(tmdb_id: int):
    if tmdb_id <= 0:
        raise HTTPException(status_code=400, detail="tmdb_id must be a positive integer")
    data = await tmdb_get(f"/movie/{tmdb_id}/videos", {"language": "en-US"})
    videos = data.get("results") or []
    result: List[VideoItem] = []
    for v in videos:
        if v.get("site") == "YouTube":
            result.append(VideoItem(
                key=v.get("key", ""),
                name=v.get("name") or "",
                site=v.get("site", ""),
                video_type=v.get("type", ""),
                official=v.get("official", False),
            ))
    priority = {"Trailer": 0, "Teaser": 1}
    result.sort(key=lambda x: (0 if x.official else 1, priority.get(x.video_type, 2)))
    return result

@app.get("/movie/id/{tmdb_id}/certification")
async def movie_certification(tmdb_id: int):
    if tmdb_id <= 0:
        raise HTTPException(status_code=400, detail="tmdb_id must be a positive integer")
    return {"tmdb_id": tmdb_id, "certification": await tmdb_certification(tmdb_id)}

@app.get("/recommend/genre", response_model=List[TMDBMovieCard])
async def recommend_genre(
    tmdb_id: int = Query(..., gt=0),
    limit: int = Query(18, ge=1, le=50),
):
    details = await tmdb_movie_details(tmdb_id)
    if not details.genres:
        return []
    genre_id = details.genres[0]["id"]
    discover = await tmdb_get("/discover/movie", {
        "with_genres": genre_id,
        "language": "en-US",
        "sort_by": "popularity.desc",
        "page": 1,
    })
    cards = await tmdb_cards_from_results(discover.get("results") or [], limit=limit + 1)
    return [c for c in cards if c.tmdb_id != tmdb_id][:limit]

@app.get("/recommend/tfidf")
async def recommend_tfidf(
    title: str = Query(..., min_length=1),
    top_n: int = Query(10, ge=1, le=50),
):
    recs = tfidf_recommend_titles(title, top_n=top_n)
    return [{"title": t, "score": s} for t, s in recs]

@app.get("/recommend/similar/{tmdb_id}", response_model=SimilarBundleResponse)
async def recommend_similar(
    tmdb_id: int,
    tfidf_top_n: int = Query(12, ge=1, le=30),
    genre_limit: int = Query(12, ge=1, le=30),
):
    if tmdb_id <= 0:
        raise HTTPException(status_code=400, detail="tmdb_id must be a positive integer")

    details = await tmdb_movie_details(tmdb_id)
    return await _build_similar_bundle(tmdb_id, details, tfidf_top_n, genre_limit)

@app.get("/movie/search", response_model=SearchBundleResponse)
async def search_bundle(
    query: str = Query(..., min_length=1),
    tfidf_top_n: int = Query(12, ge=1, le=30),
    genre_limit: int = Query(12, ge=1, le=30),
):
    best = await tmdb_search_first(query)
    if not best:
        raise HTTPException(status_code=404, detail=f"No TMDB movie found for query: '{query}'")

    raw_id = best.get("id")
    if raw_id is None:
        raise HTTPException(status_code=502, detail="TMDB returned a result with no id")

    tmdb_id = int(raw_id)
    details = await tmdb_movie_details(tmdb_id)
    bundle = await _build_similar_bundle(tmdb_id, details, tfidf_top_n, genre_limit)

    return SearchBundleResponse(
        query=query,
        movie_details=details,
        tfidf_recommendations=bundle.tfidf_recommendations,
        genre_recommendations=bundle.genre_recommendations,
    )