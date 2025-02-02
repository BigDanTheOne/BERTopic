"""
Unit tests for topic representation

This includes the following features:
    * Extracting Topics
    * Updating topics after extraction
    * Topic reduction
"""

import pytest
import numpy as np
import pandas as pd
from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import CountVectorizer

import bertopic._bertopic
from bertopic._bertopic import TopicMapper
from bertopic.backend._utils import select_backend
from bertopic import BERTopic

newsgroup_docs = fetch_20newsgroups(subset='all')['data'][:1000]


def test_extract_topics():
    """ Test Topic Extraction

    Test whether topics could be extracted using c-TF-IDF.
    Checks are related to the existence of topic representation,
    not so much whether they make sense semantically.
    """
    nr_topics = 5
    documents = pd.DataFrame({"Document": newsgroup_docs,
                              "ID": range(len(newsgroup_docs)),
                              "Topic": np.random.randint(-1, nr_topics-1, len(newsgroup_docs))})
    model = BERTopic()
    model.embedding_model = select_backend("all-MiniLM-L6-v2")
    model._update_topic_size(documents)
    model._extract_topics(documents)
    freq = model.get_topic_freq()

    assert model.c_tf_idf.shape[0] == 5
    assert model.c_tf_idf.shape[1] > 100
    assert isinstance(freq, pd.DataFrame)
    assert nr_topics == len(freq.Topic.unique())
    assert freq.Count.sum() == len(documents)
    assert len(freq.Topic.unique()) == len(freq)


def test_extract_topics_custom_cv():
    """ Test Topic Extraction with custom Countvectorizer

    Test whether topics could be extracted using c-TF-IDF.
    Checks are related to the existence of topic representation,
    not so much whether they make sense semantically.
    """
    nr_topics = 5
    documents = pd.DataFrame({"Document": newsgroup_docs,
                              "ID": range(len(newsgroup_docs)),
                              "Topic": np.random.randint(-1, nr_topics-1, len(newsgroup_docs))})

    cv = CountVectorizer(ngram_range=(1, 2))
    model = BERTopic(vectorizer_model=cv)
    model.embedding_model = select_backend("all-MiniLM-L6-v2")
    model._update_topic_size(documents)
    model._extract_topics(documents)
    freq = model.get_topic_freq()

    assert model.c_tf_idf.shape[0] == 5
    assert model.c_tf_idf.shape[1] > 100
    assert isinstance(freq, pd.DataFrame)
    assert nr_topics == len(freq.Topic.unique())
    assert freq.Count.sum() == len(documents)
    assert len(freq.Topic.unique()) == len(freq)


@pytest.mark.parametrize("reduced_topics", [1, 2, 4, 10])
def test_topic_reduction(reduced_topics):
    """ Test Topic Reduction

    The the reduction of topics after having generated
    topics. This generation of the initial topics is done
    manually as the training takes quite a while.
    """
    nr_topics = reduced_topics + 2
    model = BERTopic(nr_topics=reduced_topics)
    model.embedding_model = select_backend("all-MiniLM-L6-v2")
    topics = np.random.randint(-1, nr_topics-1, len(newsgroup_docs))
    old_documents = pd.DataFrame({"Document": newsgroup_docs,
                                  "ID": range(len(newsgroup_docs)),
                                  "Topic": topics})
    model.hdbscan_model.labels_ = topics
    model.topic_mapper = TopicMapper(model.hdbscan_model)
    model._update_topic_size(old_documents)
    old_documents = model._sort_mappings_by_frequency(old_documents)
    model._extract_topics(old_documents.copy())
    old_freq = model.get_topic_freq()

    new_documents = model._reduce_topics(old_documents.copy())
    new_freq = model.get_topic_freq()

    assert old_freq.Count.sum() == new_freq.Count.sum()
    assert len(old_freq.Topic.unique()) == len(old_freq)
    assert len(new_freq.Topic.unique()) == len(new_freq)
    assert not set(model.get_topic_freq().Topic).difference(set(new_documents.Topic))


def test_topic_reduction_edge_cases():
    """ Test Topic Reduction Large Nr Topics

    Test whether the topics are not reduced if the reduced number
    of topics exceeds the actual number of topics found
    """
    nr_topics = 5
    topics = np.random.randint(-1, nr_topics - 1, len(newsgroup_docs))
    model = BERTopic()
    model.embedding_model = select_backend("all-MiniLM-L6-v2")
    model.nr_topics = 100
    model.hdbscan_model.labels_ = topics
    old_documents = pd.DataFrame({"Document": newsgroup_docs,
                                  "ID": range(len(newsgroup_docs)),
                                  "Topic": topics})
    model._update_topic_size(old_documents)
    model._extract_topics(old_documents)
    old_freq = model.get_topic_freq()

    new_documents = model._reduce_topics(old_documents)
    new_freq = model.get_topic_freq()

    assert not set(old_documents.Topic).difference(set(new_documents.Topic))
    pd.testing.assert_frame_equal(old_documents, new_documents)
    pd.testing.assert_frame_equal(old_freq, new_freq)
