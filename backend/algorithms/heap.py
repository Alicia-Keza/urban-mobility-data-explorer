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
    
    def add(self,value,zone):
        self.items.append((value,zone)) #put new item at the end
        self.bubble_up (len(self.items) - 1) #let it climb to its spot
    
    def bubble_up(self,i):
        #move an item up while it is smaller than its parent
        while i > 0:
            parent = (i - 1) // 2
            if self.items[i][0] < self.items[parent][0]:
                self.items[i], self.items[parent] = self.items[parent], self.items[i] #swap
                i = parent #keep climbing from the parent's spot
            else:
                break #parent is already smaller, so stop
    
    def bubble_down(self,i):
        #move an item down while a child is smaller than it
        n = len(self.items)
        while True:
            left = 2 * i + 1
            right = 2 * i + 2
            smallest = i #assume the current item is smallest for now
            if left < n and self.items[left][0] < self.items[smallest][0]:
                smallest = left #left child is smaller
            if right < n and self.items[right][0] < self.items[smallest][0]:
                smallest = right #right child is smaller
            if smallest == i:
                break #item is already smaller than both children, so stop
            self.items[i], self.items[smallest] = self.items[smallest], self.items[i] #swap
            i = smallest #keep sinking from the smallest child's spot  

    def replace_smallest(self,value,zone):
        self.items[0] = (value,zone) #overwrite the front item
        self.bubble_down(0) #let it sink to its spot    

    def take_smallest(self):
        front = self.items[0] #remember the front (smallest) item
        last = self.items.pop() #remove the last item
        if self.items: #if the heap isn't empty now
            self.items[0] = last #move that last item to the front
            self.bubble_down(0) #let it sink so the heap stays valid
        return front #give back the item we removed
    
     