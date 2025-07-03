from aligner import initial_grouping, merge_on_sentence_boundary

words = [
    {'text': 'Hello', 'start': 0.0, 'end': 0.5, 'speaker_id': 'A'},
    {'text': 'world.', 'start': 0.6, 'end': 1.0, 'speaker_id': 'A'},
    {'text': 'How', 'start': 4.0, 'end': 4.2, 'speaker_id': 'A'},
    {'text': 'are', 'start': 4.3, 'end': 4.5, 'speaker_id': 'A'},
    {'text': 'you?', 'start': 4.6, 'end': 5.0, 'speaker_id': 'A'},
    {'text': 'I', 'start': 5.1, 'end': 5.2, 'speaker_id': 'B'},
    {'text': 'am', 'start': 5.3, 'end': 5.4, 'speaker_id': 'B'},
    {'text': 'fine.', 'start': 5.5, 'end': 6.0, 'speaker_id': 'B'}
]

initial = initial_grouping(words)
print('Initial segments:', len(initial))
for i, seg in enumerate(initial):
    texts = [w['text'] for w in seg]
    speaker = seg[0]['speaker_id']
    print(f'  Segment {i}: {texts} - Speaker {speaker}')
    
merged = merge_on_sentence_boundary(initial)
print('Merged segments:', len(merged))
for i, seg in enumerate(merged):
    texts = [w['text'] for w in seg]
    speaker = seg[0]['speaker_id']
    print(f'  Segment {i}: {texts} - Speaker {speaker}')
