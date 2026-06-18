#Find the top K taxi zones using a min-heap we build by hand.
#no python shortcuts (no heapq, no sorted) - we write the heap ourselves.
#
#A min-heap is a list where the smallest value is always at the front (index 0).
#We keep at most K items. For each zone:
#   - if the heap isn't full, add it
#   - if it's full and the new zone beats the smallest one we kept, swap it in
#At the end, the heap holds the K biggest zones.
#
#Why a heap and not sorting? Sorting all the zones is wasteful when we only
#need a few. The heap only ever holds K items, so it does less work.
#
#Where each item sits in the list, for the item at position i:
#   - parent is at      (i - 1) // 2
#   - left child is at  2 * i + 1
#   - right child is at 2 * i + 2
#Rule we always keep: every parent is smaller than its children. That rule keeps the smallest item at the front.

class MinHeap:
    def __init__(self):
        self.items = [] #each item is a pair: (value, zone)

    def size(self):
        return len(self.items) #how many items are in the heap
    
    def smallest(self):
        return self.items[0] #smallest item is always at the front
    
    