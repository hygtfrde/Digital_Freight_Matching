"""
Unit tests for NetworkCache class.

Tests caching, expiration, thread safety, and LRU eviction functionality.
"""

import pytest
import time
import threading
from datetime import datetime, timedelta
from services.route_calculation import NetworkCache, BoundingBox


class TestNetworkCache:
    """Test cases for NetworkCache class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cache = NetworkCache(max_age_hours=1, max_cache_size=3)
        self.bbox1 = BoundingBox(north=34.0, south=33.0, east=-84.0, west=-85.0)
        self.bbox2 = BoundingBox(north=35.0, south=34.0, east=-83.0, west=-84.0)
        self.mock_graph1 = Mock()
        self.mock_graph2 = Mock()
    
    def test_cache_initialization(self):
        """Test cache initialization with parameters."""
        cache = NetworkCache(max_age_hours=2, max_cache_size=10)
        
        assert cache.max_age_hours == 2
        assert cache.max_cache_size == 10
        assert len(cache.cache) == 0
        assert len(cache.cache_times) == 0
        assert len(cache.cache_access_times) == 0
    
    def test_bbox_to_key_conversion(self):
        """Test bounding box to cache key conversion."""
        key1 = self.cache._bbox_to_key(self.bbox1)
        key2 = self.cache._bbox_to_key(self.bbox2)
        
        assert isinstance(key1, str)
        assert isinstance(key2, str)
        assert key1 != key2
        
        # Same bbox should produce same key
        key1_duplicate = self.cache._bbox_to_key(self.bbox1)
        assert key1 == key1_duplicate
    
    def test_cache_and_retrieve_network(self):
        """Test basic caching and retrieval."""
        # Cache should be empty initially
        assert self.cache.get_network(self.bbox1) is None
        
        # Cache a network
        self.cache.cache_network(self.bbox1, self.mock_graph1)
        
        # Should be able to retrieve it
        retrieved = self.cache.get_network(self.bbox1)
        assert retrieved is self.mock_graph1
    
    def test_cache_none_graph(self):
        """Test handling of None graph caching."""
        # Should not cache None graphs
        self.cache.cache_network(self.bbox1, None)
        
        # Should still return None (not cached)
        assert self.cache.get_network(self.bbox1) is None
        assert len(self.cache.cache) == 0
    
    def test_cache_miss(self):
        """Test cache miss for non-existent entry."""
        # Cache one bbox
        self.cache.cache_network(self.bbox1, self.mock_graph1)
        
        # Different bbox should be cache miss
        assert self.cache.get_network(self.bbox2) is None
    
    def test_cache_expiration(self):
        """Test cache entry expiration."""
        # Cache with very short expiration
        short_cache = NetworkCache(max_age_hours=0.001)  # ~3.6 seconds
        short_cache.cache_network(self.bbox1, self.mock_graph1)
        
        # Should be available immediately
        assert short_cache.get_network(self.bbox1) is self.mock_graph1
        
        # Manually set cache time to past
        cache_key = short_cache._bbox_to_key(self.bbox1)
        short_cache.cache_times[cache_key] = datetime.now() - timedelta(hours=1)
        
        # Should be expired now
        assert short_cache.get_network(self.bbox1) is None
        
        # Entry should be removed from cache
        assert cache_key not in short_cache.cache
    
    def test_lru_eviction(self):
        """Test LRU (Least Recently Used) eviction."""
        # Fill cache to capacity
        bbox3 = BoundingBox(north=36.0, south=35.0, east=-82.0, west=-83.0)
        
        self.cache.cache_network(self.bbox1, self.mock_graph1)
        self.cache.cache_network(self.bbox2, self.mock_graph2)
        self.cache.cache_network(bbox3, Mock())
        
        assert len(self.cache.cache) == 3
        
        # Access bbox1 to make it recently used
        self.cache.get_network(self.bbox1)
        
        # Add one more (should evict bbox2 as it's least recently used)
        bbox4 = BoundingBox(north=37.0, south=36.0, east=-81.0, west=-82.0)
        self.cache.cache_network(bbox4, Mock())
        
        # Should still have 3 entries
        assert len(self.cache.cache) == 3
        
        # bbox1 should still be there (recently accessed)
        assert self.cache.get_network(self.bbox1) is self.mock_graph1
        
        # bbox2 should be evicted
        assert self.cache.get_network(self.bbox2) is None
    
    def test_clear_expired_cache(self):
        """Test clearing expired cache entries."""
        # Add some entries
        self.cache.cache_network(self.bbox1, self.mock_graph1)
        self.cache.cache_network(self.bbox2, self.mock_graph2)
        
        # Manually expire one entry
        cache_key1 = self.cache._bbox_to_key(self.bbox1)
        self.cache.cache_times[cache_key1] = datetime.now() - timedelta(hours=2)
        
        # Clear expired entries
        removed_count = self.cache.clear_expired_cache()
        
        assert removed_count == 1
        assert self.cache.get_network(self.bbox1) is None  # Expired
        assert self.cache.get_network(self.bbox2) is self.mock_graph2  # Still valid
    
    def test_clear_expired_with_custom_age(self):
        """Test clearing expired cache with custom max age."""
        self.cache.cache_network(self.bbox1, self.mock_graph1)
        
        # Entry should not be expired with default age
        removed_count = self.cache.clear_expired_cache()
        assert removed_count == 0
        
        # Manually set cache time to be older than the custom age
        cache_key1 = self.cache._bbox_to_key(self.bbox1)
        self.cache.cache_times[cache_key1] = datetime.now() - timedelta(hours=0.002)
        
        # But should be expired with very short custom age
        removed_count = self.cache.clear_expired_cache(max_age_hours=0.001)
        assert removed_count == 1
    
    def test_clear_all_cache(self):
        """Test clearing all cache entries."""
        # Add some entries
        self.cache.cache_network(self.bbox1, self.mock_graph1)
        self.cache.cache_network(self.bbox2, self.mock_graph2)
        
        assert len(self.cache.cache) == 2
        
        # Clear all
        removed_count = self.cache.clear_all()
        
        assert removed_count == 2
        assert len(self.cache.cache) == 0
        assert len(self.cache.cache_times) == 0
        assert len(self.cache.cache_access_times) == 0
    
    def test_cache_stats(self):
        """Test cache statistics."""
        # Empty cache stats
        stats = self.cache.get_cache_stats()
        
        assert stats["total_entries"] == 0
        assert stats["expired_entries"] == 0
        assert stats["max_cache_size"] == 3
        assert stats["max_age_hours"] == 1
        assert stats["cache_utilization"] == 0.0
        
        # Add some entries
        self.cache.cache_network(self.bbox1, self.mock_graph1)
        self.cache.cache_network(self.bbox2, self.mock_graph2)
        
        # Expire one entry
        cache_key1 = self.cache._bbox_to_key(self.bbox1)
        self.cache.cache_times[cache_key1] = datetime.now() - timedelta(hours=2)
        
        stats = self.cache.get_cache_stats()
        
        assert stats["total_entries"] == 2
        assert stats["expired_entries"] == 1
        assert stats["cache_utilization"] == 66.7  # 2/3 * 100
    
    def test_contains_bbox(self):
        """Test checking if bbox is in cache."""
        # Should not contain initially
        assert not self.cache.contains_bbox(self.bbox1)
        
        # Cache it
        self.cache.cache_network(self.bbox1, self.mock_graph1)
        
        # Should contain now
        assert self.cache.contains_bbox(self.bbox1)
        
        # Should not contain different bbox
        assert not self.cache.contains_bbox(self.bbox2)
        
        # Expire the entry
        cache_key1 = self.cache._bbox_to_key(self.bbox1)
        self.cache.cache_times[cache_key1] = datetime.now() - timedelta(hours=2)
        
        # Should not contain expired entry
        assert not self.cache.contains_bbox(self.bbox1)
    
    def test_bbox_overlap_detection(self):
        """Test bounding box overlap detection."""
        bbox1 = BoundingBox(north=34.0, south=33.0, east=-84.0, west=-85.0)
        bbox2 = BoundingBox(north=34.5, south=33.5, east=-84.5, west=-85.5)  # Overlaps
        bbox3 = BoundingBox(north=32.0, south=31.0, east=-83.0, west=-84.0)  # No overlap
        
        # Test overlap detection
        assert self.cache._bboxes_overlap(bbox1, bbox2)  # Should overlap
        assert not self.cache._bboxes_overlap(bbox1, bbox3)  # Should not overlap
        
        # Test symmetric property
        assert self.cache._bboxes_overlap(bbox2, bbox1)
    
    def test_get_bbox_coverage(self):
        """Test finding overlapping cached bounding boxes."""
        # Cache some bboxes
        bbox_overlap = BoundingBox(north=34.5, south=33.5, east=-84.5, west=-85.5)
        bbox_no_overlap = BoundingBox(north=32.0, south=31.0, east=-83.0, west=-84.0)
        
        self.cache.cache_network(self.bbox1, self.mock_graph1)
        self.cache.cache_network(bbox_overlap, Mock())
        self.cache.cache_network(bbox_no_overlap, Mock())
        
        # Find coverage for a target bbox
        target_bbox = BoundingBox(north=34.2, south=33.2, east=-84.2, west=-85.2)
        overlapping = self.cache.get_bbox_coverage(target_bbox)
        
        # Should find the overlapping ones
        assert len(overlapping) >= 1  # At least bbox1 and bbox_overlap should match
        
        # Verify the overlapping bboxes actually overlap
        for bbox in overlapping:
            assert self.cache._bboxes_overlap(target_bbox, bbox)
    
    def test_thread_safety(self):
        """Test thread safety of cache operations."""
        results = []
        errors = []
        
        def cache_worker(worker_id):
            """Worker function for threading test."""
            try:
                bbox = BoundingBox(
                    north=34.0 + worker_id * 0.1,
                    south=33.0 + worker_id * 0.1,
                    east=-84.0 + worker_id * 0.1,
                    west=-85.0 + worker_id * 0.1
                )
                graph = Mock()
                
                # Cache and retrieve multiple times
                for i in range(10):
                    self.cache.cache_network(bbox, graph)
                    retrieved = self.cache.get_network(bbox)
                    if retrieved is not graph:
                        errors.append(f"Worker {worker_id}: Retrieved wrong graph")
                    
                    # Also test stats and cleanup
                    if i % 3 == 0:
                        self.cache.get_cache_stats()
                        self.cache.clear_expired_cache()
                
                results.append(f"Worker {worker_id} completed")
                
            except Exception as e:
                errors.append(f"Worker {worker_id} error: {e}")
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=cache_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 5, f"Not all workers completed: {results}"
    
    def test_access_time_updates(self):
        """Test that access times are properly updated."""
        # Cache an entry
        self.cache.cache_network(self.bbox1, self.mock_graph1)
        
        cache_key = self.cache._bbox_to_key(self.bbox1)
        initial_access_time = self.cache.cache_access_times[cache_key]
        
        # Wait a bit and access again
        time.sleep(0.01)
        self.cache.get_network(self.bbox1)
        
        updated_access_time = self.cache.cache_access_times[cache_key]
        
        # Access time should be updated
        assert updated_access_time > initial_access_time
    
    def test_is_expired_method(self):
        """Test the _is_expired helper method."""
        current_time = datetime.now()
        
        # Recent time should not be expired
        recent_time = current_time - timedelta(minutes=30)
        assert not self.cache._is_expired(recent_time, max_age_hours=1)
        
        # Old time should be expired
        old_time = current_time - timedelta(hours=2)
        assert self.cache._is_expired(old_time, max_age_hours=1)
        
        # Test with custom max age
        assert not self.cache._is_expired(old_time, max_age_hours=3)
        assert self.cache._is_expired(old_time, max_age_hours=0.5)


if __name__ == "__main__":
    pytest.main([__file__])