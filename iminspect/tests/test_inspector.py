#!/usr/bin/env python
# coding=utf-8

"""
Very simple test suite (as most of the functionality is GUI-based and thus,
rather complex to test).
"""

import pytest
from ..inspector import fmti, fmtb, fmtf, fmt1f, fmt2f, fmt3f, fmt4f, \
    FilenameUtils, Inspector


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

    #TODO same for ensure flow extension and ensureFileExtension
    assert FilenameUtils.ensureFlowExtension(None) is None

    assert FilenameUtils.ensureFileExtension(None, []) is None
    with pytest.raises(ValueError):
        FilenameUtils.ensureFileExtension('', ['foo'])
    with pytest.raises(ValueError):
        FilenameUtils.ensureFileExtension('foo', [])


def test_saving(tmp_path):
    out_fn = tmp_path / 'save-test.png'
    import os
    print(str(out_fn))
    out_fn.write_text("FOO")
    assert os.path.exists(out_fn)
    #TODO use str(out_fn) to store....
    # see http://doc.pytest.org/en/latest/tmpdir.html for tmp_path fixture
