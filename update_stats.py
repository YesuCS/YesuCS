#!/usr/bin/env python3
"""
Refresh the numbers in profile.json from the GitHub API, then re-render.
Run by .github/workflows/refresh.yml; GITHUB_TOKEN is enough (public data only).
"""
import json, os, sys, urllib.error, urllib.request

API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN", "")


def get(path):
    req = urllib.request.Request(API + path,
                                 headers={"Accept": "application/vnd.github+json",
                                          "User-Agent": "profile-refresh"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    cfg = json.load(open("profile.json"))
    user = cfg["user"]
    stats = dict(cfg["stats"])

    try:
        me = get(f"/users/{user}")
        stats["followers"] = me["followers"]
        stats["repos"] = me["public_repos"]

        repos, page = [], 1
        while True:
            batch = get(f"/users/{user}/repos?per_page=100&page={page}&type=owner")
            repos += batch
            if len(batch) < 100:
                break
            page += 1
        stats["stars"] = sum(r["stargazers_count"] for r in repos)

        langs = {}
        for r in repos:
            if r.get("language"):
                langs[r["language"]] = langs.get(r["language"], 0) + 1
        if langs:
            top, n = max(langs.items(), key=lambda kv: kv[1])
            stats["top_language"] = top
            stats["top_language_pct"] = round(n / sum(langs.values()) * 100)

        commits = get(f"/search/commits?q=author:{user}&per_page=1")
        stats["commits"] = commits["total_count"]
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError) as e:
        # Never fail the run over a flaky API - keep the numbers we already have.
        print(f"warning: stats refresh incomplete ({e}); keeping existing values",
              file=sys.stderr)

    cfg["stats"] = stats
    with open("profile.json", "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
    print("stats:", json.dumps(stats))


if __name__ == "__main__":
    main()
