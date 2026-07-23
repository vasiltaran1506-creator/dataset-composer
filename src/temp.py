import random
from collections import Counter
from scene import Scene
from scene_builder import SceneBuilder
from config_loader import CharacterPersonality

p = CharacterPersonality.from_dict({'modes': [{
    'id': 'default', 'weight': 1.0,
    'axes': {
        'expression': {'mood': {'shy': 5.0, 'smirk': 0.0}},
        'pose':       {'base': {'sitting': 5.0}},
        'action':     {'shouting': 0.0, 'reading': 3.0},
    }
}]})
m = p.sample_mode(random)

# 1. Точные веса характера
assert p.is_neutral() is False
assert SceneBuilder._char_weight(m, 'action', 'shouting') == 0.0
assert SceneBuilder._char_weight(m, 'action', 'reading') == 3.0
assert SceneBuilder._char_weight(m, 'action', 'walking') == 1.0   # не упомянут => нейтрально
print("char_weight OK")

# 2. avoid в слоте => тег НЕ выбирается никогда (детерминированно)
idx = {'mood': ['shy', 'happy', 'smirk'], 'base': ['sitting', 'standing']}
for _ in range(300):
    assert SceneBuilder._choose_slot_tag('mood', m, idx, [], ['smirk']) != 'smirk'
print("avoid-slot OK (300 выборок без banned-тега)")

# 3. prefer доминирует (shy вес 5*3=15 против happy=1; smirk забанен)
c = Counter(SceneBuilder._choose_slot_tag('mood', m, idx, ['shy'], ['smirk']) for _ in range(1000))
print("mood distribution:", dict(c))
assert c.get('shy', 0) > c.get('happy', 0) * 5

# 4. _apply_pose пишет в composite-поля (sitting доминирует: 5*3=15 vs standing=1)
sc = Scene()
SceneBuilder._apply_pose(sc, m, idx, ['sitting'], [])
print("pose_base =", sc.pose_base)
assert sc.pose_base == 'sitting'

# 5. _apply_face для НЕ-neutral => composite-поля лица
SceneBuilder._apply_face(sc, m, idx, ['shy'], ['smirk'], neutral=False)
print("face_mood =", sc.face_mood)
assert sc.face_mood == 'shy'

# 6. _apply_face для neutral => старый плоский expression (поведение до фазы 2)
sc2 = Scene()
SceneBuilder._apply_face(sc2, m, idx, ['happy', 'smirk'], [], neutral=True)
print("neutral flat expression =", sc2.expression)
assert sc2.expression in ('happy', 'smirk')

# 7. neutral-характер: множители = 1, выбор равномерный по prefers мира
pn = CharacterPersonality.from_dict(None)
mn = pn.sample_mode(random)
assert pn.is_neutral() is True
assert SceneBuilder._char_weight(mn, 'action', 'shouting') == 1.0
print("neutral profile OK")

print("\nALL PHASE-2 RESOLVER CHECKS PASSED")