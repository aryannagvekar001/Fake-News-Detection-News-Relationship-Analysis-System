"""
backend/hash_table.py
Custom Hash Table implementation with Separate Chaining for collision resolution.

DSA CONCEPT: Hash Table (Dictionary)
- A hash table stores key-value pairs.
- A hash function maps keys to indices (buckets).
- Collision: two different keys mapped to the same index.
- Separate Chaining: each bucket holds a linked list of (key, value) pairs.

Time Complexity:
- Average case: O(1) for insert, lookup, delete
- Worst case: O(n) if all keys collide (rare with a good hash function)

This custom implementation is for educational demonstration purposes.
Python's built-in dict is also a hash table and is used alongside this.
"""

from typing import Any, List, Optional, Tuple


class HashNode:
    """A single node in the separate chaining linked list."""
    def __init__(self, key: str, value: Any):
        self.key = key
        self.value = value  # Can be a list for multi-value storage
        self.next: Optional['HashNode'] = None


class HashTable:
    """
    Custom Hash Table with Separate Chaining.

    Used for: Keyword → [Article IDs] mapping.

    Example:
        table.insert("technology", "A01")
        table.insert("technology", "A05")
        table.lookup("technology") → ["A01", "A05"]

    Parameters:
        size (int): Number of buckets in the hash table.
                    Larger size = fewer collisions, more memory.
    """

    def __init__(self, size: int = 256):
        self.size = size
        self.buckets: List[Optional[HashNode]] = [None] * self.size
        self.count = 0  # Total number of key-value pairs stored
        self.collision_count = 0  # For demonstration: track collisions

    def _hash(self, key: str) -> int:
        """
        Hash Function: Maps a string key to a bucket index.

        Algorithm: Polynomial Rolling Hash
        hash = sum(ord(char) * prime^i) mod table_size

        This distributes keys uniformly across buckets.
        """
        prime = 31
        h = 0
        for i, char in enumerate(key.lower()):
            h = (h + ord(char) * (prime ** i)) % self.size
        return h

    def insert(self, key: str, value: Any) -> None:
        """
        Insert a key-value pair into the hash table.
        If the key exists, append the value to its list (for multi-value support).
        """
        index = self._hash(key)
        head = self.buckets[index]

        # Search for existing key in the chain
        current = head
        while current:
            if current.key == key:
                # Key exists — append to value list if not duplicate
                if isinstance(current.value, list):
                    if value not in current.value:
                        current.value.append(value)
                else:
                    if current.value != value:
                        current.value = [current.value, value]
                return
            current = current.next

        # Key not found — insert at head of chain
        new_node = HashNode(key, [value] if not isinstance(value, list) else value)
        if head is not None:
            self.collision_count += 1  # Count collisions for DSA demonstration
            new_node.next = head
        self.buckets[index] = new_node
        self.count += 1

    def lookup(self, key: str) -> Optional[Any]:
        """
        Look up a key in the hash table.
        Returns the value (list of article IDs) or None if not found.

        Time Complexity: O(1) average, O(n) worst case
        """
        index = self._hash(key)
        current = self.buckets[index]

        while current:
            if current.key == key:
                return current.value
            current = current.next

        return None  # Key not found

    def delete(self, key: str) -> bool:
        """
        Delete a key from the hash table.
        Returns True if deleted, False if not found.
        """
        index = self._hash(key)
        current = self.buckets[index]
        prev = None

        while current:
            if current.key == key:
                if prev:
                    prev.next = current.next
                else:
                    self.buckets[index] = current.next
                self.count -= 1
                return True
            prev = current
            current = current.next

        return False

    def get_all_keys(self) -> List[str]:
        """Return all keys in the hash table."""
        keys = []
        for bucket in self.buckets:
            current = bucket
            while current:
                keys.append(current.key)
                current = current.next
        return keys

    def get_all_items(self) -> List[Tuple[str, Any]]:
        """Return all (key, value) pairs in the hash table."""
        items = []
        for bucket in self.buckets:
            current = bucket
            while current:
                items.append((current.key, current.value))
                current = current.next
        return items

    def get_load_factor(self) -> float:
        """
        Load Factor = number of items / number of buckets.
        A high load factor (> 0.7) means more collisions.
        Used to decide when to resize the table.
        """
        return self.count / self.size

    def get_bucket_info(self) -> dict:
        """
        Return information about bucket usage.
        Useful for demonstrating hash distribution in the UI.
        """
        non_empty = sum(1 for b in self.buckets if b is not None)
        max_chain = 0
        for bucket in self.buckets:
            chain_len = 0
            current = bucket
            while current:
                chain_len += 1
                current = current.next
            max_chain = max(max_chain, chain_len)

        return {
            "total_buckets": self.size,
            "used_buckets": non_empty,
            "empty_buckets": self.size - non_empty,
            "total_entries": self.count,
            "load_factor": round(self.get_load_factor(), 3),
            "collisions": self.collision_count,
            "max_chain_length": max_chain
        }

    def __len__(self) -> int:
        return self.count

    def __repr__(self) -> str:
        return f"HashTable(size={self.size}, entries={self.count}, load_factor={self.get_load_factor():.3f})"
