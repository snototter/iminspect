#!/usr/bin/env python
# coding=utf-8

"""
Very simple test suite (as most of the functionality is GUI-based and thus,
rather complex to test).
"""

import pytest
from ..inspection_utils import fmti, fmtb, fmtf, fmt1f, fmt2f, fmt3f, fmt4f, FilenameUtils


def test_fmtb():
    assert fmtb(True) == 'True'
    assert fmtb(False) == 'False'
    assert fmtb(0) == 'False'
    assert fmtb(-17) == 'True'


def test_fmti():
    assert fmti(3) == '3'
    assert fmti(-0) == '0'
    assert fmti(-42) == '-42'


def test_fmtf():
    assert fmtf(3) == '{:f}'.format(3)
    assert fmtf(17.0099123) == '{:f}'.format(17.0099123)


def test_fmt1f():
    assert fmt1f(3) == '3.0'
    assert fmt1f(17.0099123) == '17.0'
    assert fmt1f(-12.08) == '-12.1'


def test_fmt2f():
    assert fmt2f(3) == '3.00'
    assert fmt2f(17.0099123) == '17.01'
    assert fmt2f(-12.08) == '-12.08'


def test_fmt3f():
    assert fmt3f(3) == '3.000'
    assert fmt3f(17.0099123) == '17.010'
    assert fmt3f(-12.08) == '-12.080'


def test_fmt4f():
    assert fmt4f(3) == '3.0000'
    assert fmt4f(17.0099123) == '17.0099'
    assert fmt4f(-12.08) == '-12.0800'


def test_FilenameUtils():
    assert FilenameUtils.ensureImageExtension(None) is None
    with pytest.raises(ValueError):
        FilenameUtils.ensureImageExtension('')
    assert FilenameUtils.ensureImageExtension('foo') == 'foo.png'
    assert FilenameUtils.ensureImageExtension('foo.jpEG') == 'foo.jpEG'
    assert FilenameUtils.ensureImageExtension('FoO.pNg') == 'FoO.pNg'
    assert FilenameUtils.ensureImageExtension('FoO.pNgGg') == 'FoO.pNgGg.png'

    assert FilenameUtils.ensureFlowExtension(None) is None
    with pytest.raises(ValueError):
        FilenameUtils.ensureFlowExtension('')
    assert FilenameUtils.ensureFlowExtension('foo') == 'foo.flo'
    assert FilenameUtils.ensureFlowExtension('foo.jpEG') == 'foo.jpEG.flo'
    assert FilenameUtils.ensureFlowExtension('FoO.flow') == 'FoO.flow.flo'
    assert FilenameUtils.ensureFlowExtension('FoO.FlO') == 'FoO.FlO'

    assert FilenameUtils.ensureFileExtension(None, []) is None
    with pytest.raises(ValueError):
        FilenameUtils.ensureFileExtension('', ['foo'])
    with pytest.raises(ValueError):
        FilenameUtils.ensureFileExtension('foo', [])
    assert FilenameUtils.ensureFileExtension('foo.bar', ['bla', 'bar']) == 'foo.bar'
    assert FilenameUtils.ensureFileExtension('f00.BaR', ['bla', 'bar']) == 'f00.BaR'
    assert FilenameUtils.ensureFileExtension('foo.barz', ['bla', 'bar']) == 'foo.barz.bla'
