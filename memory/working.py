# memory/working_memory.py
# from collections import deque

# class WorkingMemory:
#     def __init__(self, limit=5):
#         self.memory = deque(maxlen=limit)

#     def add_turn(self, speaker, text):
#         self.memory.append({"speaker": speaker, "text": text})

#     def get_context(self):
#         return "\n".join([f"{m['speaker']}: {m['text']}" for m in self.memory])
