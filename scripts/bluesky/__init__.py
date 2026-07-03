"""aaron.chat Bluesky integration.

The full AT Protocol capability set the wizard's Bluesky roster covers.
Each submodule owns one slice of the API surface — see docs/bluesky-menu.html
for the roadmap this implements.

Layout:
  client.py       — authenticated atproto.Client with session caching + refresh
  facets.py       — build rich-text facets (link/mention/hashtag) from post text
  posts.py        — create text/reply/quote/repost/delete + threadgates/postgates
  media.py        — upload images/video + link-card OG fetching + aspect ratios
  profile.py      — display name / bio / avatar / banner / pinned post   (Phase E)
  identity.py     — recovery keys, app password management                (Phase E)
  graph.py        — follow / block / mute / lists                         (Phase F)
  engagement.py   — like / bookmark / report / viewer state               (Phase F)
  starterpack.py  — build reference-list + starter-pack records           (Phase F)
  reading.py      — timeline / notifications / search / thread views      (Phase G)
  chat.py         — DMs, group convos, reactions                          (Phase G)
  feeds.py        — publish feed generator record                         (Phase G)
  preferences.py  — muted words, saved/pinned feeds, thread sort          (Phase G)
  analytics.py    — nightly engagement snapshot, competitor search        (Phase H)

All submodules take an atproto.Client from client.get_client() as their first
argument. Session state persists in content/.bluesky_session.json.
"""
