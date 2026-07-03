"""Mastodon posting + admin surface for aaron.chat.

Layout mirrors scripts/bluesky/ — the publisher (mastodon_publish.py) and the
one-shot admin tools live one level up in scripts/*.

Modules:
    client       OAuth session wrapper (instance-aware)
    posts        create / reply / edit / delete / boost / quote / schedule
    media        images / video / audio / GIFV / alt-text / focal points / polls
    profile      profile update, custom fields, featured tags, pinned status,
                 endorsed accounts, preferences
    graph        follow/unfollow accounts+hashtags, requests, mute, block, lists
    engagement   favourite, bookmark, poll voting
    reading      home / public / hashtag / list timelines, search, notifications,
                 trends, suggestions, instance info, announcements
    chat         direct messages via visibility=direct, conversations, read markers
    filters      v2 filters + legacy v1 muted words
    analytics    engagement snapshots + competitor rollups + hashtag momentum

Everything works against any Mastodon-compatible instance (mastodon.social,
Glitch, Hometown, Firefish forks). Instance-specific limits (post length,
media size) are read from /api/v1/instance and can be honored via
reading.get_instance_limits().
"""
