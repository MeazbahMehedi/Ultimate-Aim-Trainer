import csv
import json
import pytest
from aimtrainer.storage import Store
from aimtrainer.model import Session,Settings


def row(mode='classic',score=100):
    s=Session(mode,seed=1);s.score=score;s.finish('Session complete');return s.summary()


def test_roundtrip_profiles(tmp_path):
    s=Store(tmp_path);s.create('Meazbah');s.set_settings(Settings(difficulty='Hard'));s.add(row())
    loaded=Store(tmp_path)
    assert loaded.active=='Meazbah' and loaded.settings.difficulty=='Hard' and loaded.sessions[0]['score']==100
    loaded.select('Player');assert loaded.sessions==[] and loaded.settings.difficulty=='Medium'


@pytest.mark.parametrize('name',['','  ','a'*25,'Player','player'])
def test_invalid_name(tmp_path,name):
    with pytest.raises(ValueError):Store(tmp_path).create(name)


def test_profile_limit(tmp_path):
    s=Store(tmp_path)
    for i in range(19):s.create(f'Profile {i}')
    with pytest.raises(ValueError):s.create('Too many')


def test_grouped_bests_exclude_practice_and_early_end(tmp_path):
    s=Store(tmp_path);s.add(row(score=100));s.add(row(score=200));s.add(row('practice',999))
    r=row('precision',300);r['difficulty']='Hard';s.add(r)
    r=row(score=999);r['reason']='Ended early';s.add(r)
    assert sorted(r['score'] for r in s.bests())==[200,300]


def test_csv_formula_safety(tmp_path):
    s=Store(tmp_path);r=row();r['reason']='=1+1';s.add(r);path=s.export()
    assert path.read_bytes().startswith(b'\xef\xbb\xbf')
    with path.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    assert rows[0]['reason']=="'=1+1"


@pytest.mark.parametrize('damaged',['{broken','[]','{"schema":999}','{"schema":2,"profiles":{}}'])
def test_recovery_preserves_original_bytes(tmp_path,damaged):
    (tmp_path/'progress.json').write_text(damaged);s=Store(tmp_path)
    assert s.active=='Player' and s.notice
    assert list(tmp_path.glob('progress-recovery-*.json'))[0].read_text()==damaged
    assert s.save() and Store(tmp_path).active=='Player'


def test_bad_record_skipped(tmp_path):
    s=Store(tmp_path);s.add(row());data=json.loads(s.path.read_text())
    data['profiles']['Player']['sessions'].append({'mode':'classic','difficulty':'Medium','date':'x','score':'oops','elapsed':1,'accuracy':50})
    s.path.write_text(json.dumps(data));assert len(Store(tmp_path).sessions)==1


def test_write_failure_keeps_memory_and_cleans_temp(tmp_path,monkeypatch):
    s=Store(tmp_path)
    def fail(*args):raise PermissionError('denied')
    monkeypatch.setattr('aimtrainer.storage.os.replace',fail)
    _,_,saved=s.add(row())
    assert not saved and len(s.sessions)==1 and s.notice and not list(tmp_path.glob('*.tmp'))


def test_history_limit(tmp_path):
    s=Store(tmp_path);s.profile['sessions']=[row() for _ in range(1000)];s.add(row(score=321))
    assert len(s.sessions)==1000 and s.sessions[-1]['score']==321


@pytest.mark.parametrize('field,value',[('hits',{}),('duration',[]),('reason',{}),('average_hit_ms','bad'),('daily',[]),('date','bad')])
def test_malformed_session_fields_are_skipped(tmp_path,field,value):
    s=Store(tmp_path);s.add(row());data=json.loads(s.path.read_text())
    data['profiles']['Player']['sessions'][0][field]=value
    s.path.write_text(json.dumps(data));assert Store(tmp_path).sessions==[]


def test_early_abort_does_not_hide_next_personal_best(tmp_path):
    s=Store(tmp_path);r=row(score=999);r['reason']='Ended early';s.add(r)
    _,best,_=s.add(row(score=100));assert best
