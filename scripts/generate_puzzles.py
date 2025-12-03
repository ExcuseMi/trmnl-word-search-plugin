#!/usr/bin/env python3
"""
Word Search Puzzle Generator (Enhanced Difficulty Tiers)
- Supports 3500 puzzles per {grid_size}/{difficulty}
- Difficulty levels redesigned:

Easy:
  - Directions: Right, Down
  - Short & medium words
  - Minimal word overlap

Medium:
  - Directions: Right, Down, Diagonal Down-Right, Diagonal Up-Right
  - More words
  - Moderate overlap
  - Occasional backwards words (~10%)

Hard:
  - All 8 directions
  - High backwards ratio (~40%)
  - Aggressive word overlap
  - Attempts to maximize density

This script rewrites and improves the original generator.
"""

import requests
import random
import json
import time
from pathlib import Path

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
THEMES = [
    "beach", "space", "ocean", "forest", "mountain", "desert", "city",
    "music", "sports", "food", "animals", "weather", "travel",
    "technology", "art", "science", "garden", "winter", "summer",
    "spring", "autumn", "coffee", "book", "movie", "fitness",
    "cooking", "adventure", "nature", "holiday", "festival", "astronomy",
    "history", "architecture", "photography", "health", "fashion",
    "education", "business", "mythology", "fantasy", "friendship",
    "family", "home", "childhood", "nostalgia", "meditation",
    "mindfulness", "crafts", "diy", "vintage", "futurism", "minimalism",
    "luxury", "sustainability", "farming", "camping", "roadtrip",
    "nightlife", "sunrise", "sunset", "rain", "snow", "cat", "dog",
    "bird", "flower", "tree", "river", "lake", "island", "cave",
    "volcano", "concert", "theater", "painting", "sculpture", "poetry",
    "writing", "gaming", "podcast", "yoga", "cycling", "hiking",
    "surfing", "skateboarding", "baking", "vegan", "streetfood", "wine",
    "tea", "chocolate", "comedy", "romance", "mystery", "horror"
]

GRID_SIZES = [8, 10, 12, 15]
DIFFICULTIES = ["easy", "medium", "hard"]
PUZZLES_PER_COMBO = 3500

OUTPUT_DIR = Path("data")

ALL_DIRECTIONS = [
    (0, 1), (1, 0), (1, 1), (-1, 1), (0, -1), (-1, 0), (-1, -1), (1, -1)
]

FALLBACK_WORDS = [
    'PUZZLE','SEARCH','FIND','WORD','GAME','FUN','BRAIN','SOLVE','GRID','LETTERS'
]

# ------------------------------------------------------------
# Difficulty Profiles
# ------------------------------------------------------------
def get_difficulty_params(difficulty, grid_size):
    if difficulty == "easy":
        return {
            'difficulty_label': 'easy',
            'directions': [(0, 1), (1, 0)],
            'backwards_ratio': 0.0,
            'word_count': grid_size,
            'min_len': 4,
            'max_len': min(8, grid_size - 1),
            'placement_attempts': 120,
            'overlap_bias': 0.1
        }

    if difficulty == "medium":
        return {
            'difficulty_label': 'medium',
            'directions': [(0, 1), (1, 0), (1, 1), (-1, 1)],
            'backwards_ratio': 0.10,
            'word_count': max(12, int(grid_size * 0.9)),
            'min_len': 4,
            'max_len': min(10, grid_size - 1),
            'placement_attempts': 200,
            'overlap_bias': 0.4
        }

    # HARD
    return {
        'difficulty_label': 'hard',
        'directions': ALL_DIRECTIONS,
        'backwards_ratio': 0.40,
        'word_count': grid_size,
        'min_len': 3,
        'max_len': min(12, grid_size - 1),
        'placement_attempts': 400,
        'overlap_bias': 0.9
    }

# ------------------------------------------------------------
# Utility: Fetch themed words
# ------------------------------------------------------------
def fetch_theme_words(theme):
    try:
        url = f"https://api.datamuse.com/words?rel_trg={theme}&max=200"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return [w['word'].upper() for w in r.json()]
    except:
        return []

# ------------------------------------------------------------
# Word Filtering
# ------------------------------------------------------------
def filter_words(words, min_len, max_len, target_count):
    filtered = [w for w in words if min_len <= len(w) <= max_len and w.isalpha()]
    selected = []
    for w in filtered:
        if not any(w != o and (w in o or o in w) for o in filtered):
            selected.append(w)
        if len(selected) >= target_count * 5:
            break
    return selected

# ------------------------------------------------------------
# Placement Helpers
# ------------------------------------------------------------
def can_place_word(grid, word, r, c, dy, dx, size):
    er = r + (len(word) - 1) * dy
    ec = c + (len(word) - 1) * dx
    if not (0 <= er < size and 0 <= ec < size):
        return False
    for i, ch in enumerate(word):
        rr = r + i * dy
        cc = c + i * dx
        if grid[rr][cc] not in ('', ch):
            return False
    return True


def place_word(grid, word, r, c, dy, dx):
    for i, ch in enumerate(word):
        grid[r + i * dy][c + i * dx] = ch

# ------------------------------------------------------------
# Puzzle Generator
# ------------------------------------------------------------
def generate_puzzle(theme, size, params, available_words, puzzle_id):
    grid = [['' for _ in range(size)] for _ in range(size)]
    count = params['word_count']
    dirs = params['directions']
    attempts = params['placement_attempts']

    # Choose words
        # Ensure unique words and exactly grid_size count
    base_words = random.sample(list(dict.fromkeys(available_words)), min(len(available_words), size))

    placed_words = []
    solution = []

    backwards_target = int(count * params['backwards_ratio'])
    backwards_used = 0

    for word in base_words:
        w = word
        # Possibly reverse
        if backwards_used < backwards_target and random.random() < params['backwards_ratio']:
            w = w[::-1]
            backwards_used += 1

        placed = False
        for _ in range(attempts):
            dy, dx = random.choice(dirs)
            r = random.randint(0, size - 1)
            c = random.randint(0, size - 1)
            if can_place_word(grid, w, r, c, dy, dx, size):
                place_word(grid, w, r, c, dy, dx)
                pos = r * size + c
                dir_idx = ALL_DIRECTIONS.index((dy, dx))
                solution.append(f"{pos};{dir_idx};{len(w)}")
                placed_words.append(word)
                placed = True
                break

        # fallback words
        if not placed and FALLBACK_WORDS:
            for fb in FALLBACK_WORDS:
                for _ in range(attempts):
                    dy, dx = random.choice(dirs)
                    r = random.randint(0, size - 1)
                    c = random.randint(0, size - 1)
                    if can_place_word(grid, fb, r, c, dy, dx, size):
                        place_word(grid, fb, r, c, dy, dx)
                        pos = r * size + c
                        dir_idx = ALL_DIRECTIONS.index((dy, dx))
                        solution.append(f"{pos};{dir_idx};{len(fb)}")
                        placed_words.append(fb)
                        placed = True
                        break
                if placed:
                    break

    # Fill blank spaces
    for r in range(size):
        for c in range(size):
            if not grid[r][c]:
                grid[r][c] = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')

    flat_grid = ''.join(''.join(row) for row in grid)

    return {
        'id': puzzle_id,
        'theme': theme,
        'grid': flat_grid,
        'solution': ','.join(solution),
        'gridSize': size,
        'difficulty': params['difficulty_label'],
        'wordCount': len(placed_words),
        'wordlist': sorted(sorted(placed_words, key=lambda w: (len(w), w.lower())))
    }

import logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Prefetch words
    theme_cache = {}
    for theme in THEMES:
        words = fetch_theme_words(theme)
        if words:
            theme_cache[theme] = words
        time.sleep(0.25)

    for size in GRID_SIZES:
        for diff in DIFFICULTIES:
            folder = OUTPUT_DIR / str(size) / diff
            folder.mkdir(parents=True, exist_ok=True)

            params = get_difficulty_params(diff, size)

            file_counter = 1
            puzzles_made = 0

            for theme, words in theme_cache.items():
                usable = filter_words(words, params['min_len'], params['max_len'], params['word_count'])
                if len(usable) < params['word_count']:
                    continue

                while puzzles_made < PUZZLES_PER_COMBO:
                    pid = f"{size}-{diff}-{file_counter}"
                    puzzle = generate_puzzle(theme, size, params, usable, pid)
                    with open(folder / f"{file_counter}.json", 'w') as f:
                        json.dump(puzzle, f, separators=(',', ':'))

                    file_counter += 1
                    puzzles_made += 1
                    if puzzles_made >= PUZZLES_PER_COMBO:
                        break

    print("Generation complete.")


if __name__ == "__main__":
    main()
