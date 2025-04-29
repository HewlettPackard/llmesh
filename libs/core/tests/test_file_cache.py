#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the functionality of the FileCache class from 
the self_serve_platform.system.file_cache module.
It includes tests for checking if a file is cached, saving data to the cache, 
loading data from the cache, and the behavior when caching is disabled.
"""

import os
import pickle
import pytest
from self_serve_platform.system.file_cache import FileCache


@pytest.fixture
def file_cache():
    """
    Fixture to create a FileCache instance with caching enabled.
    
    Returns:
        FileCache: An instance of FileCache with caching enabled.
    """
    return FileCache({"cache_to_file":True})


def test_is_cached(file_cache, tmp_path):  # pylint: disable=W0621
    """
    Test to verify if a file is correctly identified as cached or not.
    """
    # Create a temporary file
    temp_file = tmp_path / "test_file.txt"
    temp_file.write_text("test content")
    # Check that the file is not cached
    assert not file_cache.is_cached(str(temp_file))
    # Create a cached version of the file
    cached_file = tmp_path / "test_file_cached.pkl"
    cached_file.write_text("cached content")
    # Check that the file is cached
    assert file_cache.is_cached(str(temp_file))


def test_save(file_cache, tmp_path):  # pylint: disable=W0621
    """
    Test to verify that data can be saved to the cache and correctly retrieved.
    """
    # Create a temporary file
    temp_file = tmp_path / "test_file.txt"
    data = {"key": "value"}
    # Save data to the cache
    file_cache.save(str(temp_file), data)
    # Check that the cached file exists
    cached_file = tmp_path / "test_file_cached.pkl"
    assert cached_file.exists()
    # Check that the data is correctly saved
    with open(cached_file, 'rb') as f:
        loaded_data = pickle.load(f)
    assert loaded_data == data


def test_load(file_cache, tmp_path):  # pylint: disable=W0621
    """
    Test to verify that data can be loaded from the cache.
    """
    # Create a temporary file
    temp_file = tmp_path / "test_file.txt"
    data = {"key": "value"}
    # Save data to the cache
    file_cache.save(str(temp_file), data)
    # Load data from the cache
    loaded_data = file_cache.load(str(temp_file))
    assert loaded_data == data


def test_save_cache_disabled(tmp_path):
    """
    Test to verify the behavior when caching is disabled.
    """
    # Create a FileCache instance with caching disabled
    file_cache = FileCache({"cache_to_file":False})  # pylint: disable=W0621
    temp_file = tmp_path / "test_file.txt"
    data = {"key": "value"}
    # Save data to the cache
    file_cache.save(str(temp_file), data)
    # Check that the cached file does not exist
    cached_file = tmp_path / "test_file_cached.pkl"
    assert not cached_file.exists()


def test_load_no_cache(file_cache, tmp_path):  # pylint: disable=W0621
    """
    Test to verify the behavior when loading data from a non-existent cache.
    """
    # Create a temporary file
    temp_file = tmp_path / "test_file.txt"
    # Check that loading from a non-existent cache returns None
    loaded_data = file_cache.load(str(temp_file))
    assert loaded_data is None


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
