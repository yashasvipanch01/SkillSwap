from app.services.matching import Profile, compatibility, find_circles

SKILL_IDS: dict[str, int] = {}


def profile(user_id, teach=(), learn=(), availability=(), preferences=(), verified=()):
    ids = {name: SKILL_IDS.setdefault(name, len(SKILL_IDS) + 1) for name in {*teach, *learn}}
    return Profile(
        user_id=user_id,
        teach={ids[n]: n for n in teach},
        learn={ids[n]: n for n in learn},
        verified=frozenset(ids[n] for n in verified),
        availability={a.casefold(): a for a in availability},
        preferences={p.casefold(): p for p in preferences},
    )


def test_reciprocal_match_scores_both_directions():
    me = profile(1, teach=["Figma"], learn=["Python"])
    other = profile(2, teach=["Python"], learn=["Figma"])
    match = compatibility(me, other)
    assert match.reciprocal
    assert match.teaches_me == ["Python"]
    assert match.learns_from_me == ["Figma"]
    assert match.score == 70


def test_one_way_matches_are_weighted_lower_than_reciprocal():
    me = profile(1, teach=["Figma"], learn=["Python"])
    teaches_me = compatibility(me, profile(2, teach=["Python"]))
    wants_mine = compatibility(me, profile(3, learn=["Figma"]))
    assert not teaches_me.reciprocal and not wants_mine.reciprocal
    assert teaches_me.score == 40 and wants_mine.score == 30


def test_availability_preferences_and_verified_add_bonuses():
    me = profile(1, learn=["Python"], availability=["Weekends"], preferences=["Project-based"])
    other = profile(
        2, teach=["Python"], verified=["Python"], availability=["weekends"], preferences=["project-based"]
    )
    assert compatibility(me, other).score == 40 + 5 + 15 + 10


def test_no_overlap_scores_zero():
    assert compatibility(profile(1, teach=["A"]), profile(2, teach=["B"], learn=["C"])).score == 0


def test_find_circle_of_three():
    me = profile(1, teach=["Figma"], learn=["Python"])
    b = profile(2, teach=["Writing"], learn=["Figma"])
    c = profile(3, teach=["Python"], learn=["Writing"])
    circles = find_circles(me, [b, c])
    assert len(circles) == 1
    legs = circles[0]
    assert [(leg.giver_id, leg.receiver_id, leg.skills) for leg in legs] == [
        (1, 2, ["Figma"]),
        (2, 3, ["Writing"]),
        (3, 1, ["Python"]),
    ]


def test_circles_skip_partners_who_already_match_directly():
    me = profile(1, teach=["Figma"], learn=["Python"])
    direct = profile(2, teach=["Python"], learn=["Figma"])
    third = profile(3, teach=["Python"], learn=["Python2"])
    assert find_circles(me, [direct, third]) == []


def test_matches_endpoint_ranks_and_filters(make_account):
    me = make_account("Me")
    me.set_skills(teach=["Figma"], learn=["Python"])
    me.patch("/users/me", {"availability": ["Weekends"]})

    best = make_account("Best Match")
    best.set_skills(teach=["Python"], learn=["Figma"])
    partial = make_account("Partial Match")
    partial.set_skills(teach=["Python"], learn=["Cooking"])
    unrelated = make_account("Unrelated")
    unrelated.set_skills(teach=["Cooking"], learn=["Chess"])

    results = me.get("/matches").json()
    assert [r["person"]["name"] for r in results] == ["Best Match", "Partial Match"]
    assert results[0]["reciprocal"] is True
    assert results[0]["they_teach_you"] == ["Python"]
    assert "email" not in results[0]["person"]

    everyone = me.get("/matches", params={"min_score": 0}).json()
    assert {r["person"]["name"] for r in everyone} == {"Best Match", "Partial Match", "Unrelated"}
    assert [r["person"]["name"] for r in me.get("/matches", params={"min_score": 0, "q": "unrel"}).json()] == ["Unrelated"]
    assert len(me.get("/matches", params={"limit": 1}).json()) == 1
    assert all(r["person"]["id"] != me.id for r in everyone)


def test_circles_endpoint(make_account):
    me = make_account("Me")
    me.set_skills(teach=["Figma"], learn=["Python"])
    b = make_account("Bea")
    b.set_skills(teach=["Writing"], learn=["Figma"])
    c = make_account("Cal")
    c.set_skills(teach=["Python"], learn=["Writing"])

    circles = me.get("/matches/circles").json()
    assert len(circles) == 1
    names = [(leg["giver"]["name"], leg["receiver"]["name"]) for leg in circles[0]["legs"]]
    assert names == [("Me", "Bea"), ("Bea", "Cal"), ("Cal", "Me")]
