from dataclasses import asdict
from datetime import date
import math
import pytest
from aimtrainer.model import Session, Settings, Target, MODES, ARENA, daily_seed, board_key, achievement_ids


def target(s):
    t=Target(300,300,30,2,s.elapsed-.3,age=.3);s.targets.append(t);return t


@pytest.mark.parametrize('mode',MODES)
def test_modes(mode):
    s=Session(mode,seed=1);assert s.mode==mode and s.lives==10


def test_classic_duration():
    assert Session('classic',Settings(duration=30)).duration==60


def test_only_arena_left_clicks_count():
    s=Session(seed=1);target(s)
    for pos,button in [(None,1),((300,300),3),((300,50),1),((-1,300),1)]:s.shoot(pos,button)
    assert s.shots==0
    assert s.shoot((300,300))=='hit' and s.hits==1 and s.accuracy==100


def test_miss_and_expiry_cost_lives():
    s=Session(seed=1);s.shoot((400,400));assert s.lives==9
    t=target(s);t.born=-3;s.update(1/120)
    assert s.expired==1 and s.lives==8


def test_ten_misses_end_survival():
    s=Session('survival',seed=1)
    for _ in range(11):s.shoot((400,400))
    assert s.finished and s.lives==0 and s.misses==10


def test_practice_no_life_or_time_limit():
    s=Session('practice',seed=1)
    for _ in range(30):s.shoot((400,400))
    s.update(5)
    assert s.lives==10 and not s.finished and s.duration is None
    s.finish();assert s.finished


def test_combo_gap_and_miss_reset_multiplier():
    s=Session(seed=1)
    for _ in range(4):target(s);s.shoot((300,300))
    assert s.combo==4 and s.multiplier==2 and s.score==500
    s.update(.7);assert s.combo==0 and s.multiplier==1
    target(s);s.shoot((300,300));assert s.combo==1
    s.shoot((1200,700));assert s.combo==0


def test_multiplier_cap():
    s=Session(seed=1)
    for _ in range(100):target(s);s.shoot((300,300))
    assert s.multiplier==8


def test_precision_size_and_points():
    a,b=Session(seed=2),Session('precision',seed=2);a.spawn();b.spawn()
    assert b.targets[0].radius<a.targets[0].radius
    target(b);b.shoot((300,300));assert b.score==150


@pytest.mark.parametrize('fps',[30,60,120,144,240])
def test_frame_rate_independent_timer_and_tracking(fps):
    s=Session('tracking',Settings(duration=30),seed=3)
    for _ in range(30*fps):s.update(1/fps)
    ref=Session('tracking',Settings(duration=30),seed=3);ref.update(30)
    assert s.finished and s.elapsed==30 and s.track_point==pytest.approx(ref.track_point)


def test_chunked_spawn_matches_one_update():
    a,b=Session('practice',seed=6),Session('practice',seed=6)
    for _ in range(576):a.update(1/144)
    b.update(4)
    assert a.expired==b.expired and [(t.x,t.y,t.age) for t in a.targets]==[(t.x,t.y,t.age) for t in b.targets]


def test_tracking_held_accuracy_and_score():
    s=Session('tracking',seed=3)
    for _ in range(240):s.update(1/120,s.track_point,True)
    assert s.held==pytest.approx(2) and s.tracked>1.97 and s.accuracy>98 and s.score>197
    before=s.tracked;s.update(1,s.track_point,False);assert s.tracked==before


def test_tracking_off_target():
    s=Session('tracking',seed=3);s.update(2,(-100,-100),True)
    assert s.accuracy==0 and s.score==0 and s.lives==10


def test_spawns_repeatable_separated_and_in_bounds():
    a,b=Session('practice',seed=9),Session('practice',seed=9)
    for _ in range(20):a.spawn();b.spawn()
    assert [(t.x,t.y) for t in a.targets]==[(t.x,t.y) for t in b.targets]
    x,y,w,h=ARENA
    for i,t in enumerate(a.targets):
        assert x+t.radius<=t.x<=x+w-t.radius and y+t.radius<=t.y<=y+h-t.radius
        assert all(math.dist((t.x,t.y),(o.x,o.y))>t.radius+o.radius for o in a.targets[i+1:])


def test_daily_fixed_settings_and_seed():
    s=Session('practice',Settings(difficulty='Hard',duration=120),daily=True,seed=7)
    assert (s.mode,s.duration,s.settings.difficulty,s.seed)==('precision',60,'Medium',7)
    assert daily_seed(date(2026,10,25))==daily_seed(date(2026,10,25))
    assert daily_seed(date(2026,10,25))!=daily_seed(date(2026,10,26))


def test_summary_measurements():
    s=Session(seed=1);target(s);s.shoot((300,300));s.shoot((1200,700));r=s.summary()
    assert r['accuracy']==50 and r['average_hit_ms']==300 and r['best_combo']==1


@pytest.mark.parametrize('dt',[-1,float('nan'),float('inf')])
def test_bad_time_ignored(dt):
    s=Session(seed=1);s.update(dt);assert s.elapsed==0


@pytest.mark.parametrize('data',[None,[],{'volume':True},{'difficulty':'Impossible'},{'fps':'120'}])
def test_invalid_preferences(data):
    assert Settings.from_dict(data)==Settings()


def test_settings_roundtrip():
    s=Settings(difficulty='Hard',volume=0,particles=False,spawn_interval=.4,fps=144)
    assert Settings.from_dict(asdict(s))==s


def test_board_groups():
    r=Session('precision').summary()
    assert board_key(r)!=board_key({**r,'difficulty':'Hard'})
    assert board_key(r)!=board_key({**r,'duration':30})
    assert board_key({**r,'daily':True,'challenge_date':'2026-10-25'})!=board_key(r)


def test_achievement_evidence():
    r={'hits':20,'shots':20,'accuracy':100,'best_combo':12,'mode':'precision','daily':True,'reason':'Session complete'}
    assert {'first_hit','sharp_eye','in_flow','daily_done'}<=achievement_ids([r])
    assert 'consistent' in achievement_ids([r]*10) and achievement_ids([])==set()
