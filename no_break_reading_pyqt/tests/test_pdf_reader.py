import pymupdf as fitz
import pytest

from core.pdf_reader import PDFReader
from config import PDF_CONFIG


@pytest.fixture
def pdf_path(tmp_path):
    doc = fitz.open()
    for i in range(3):
        page = doc.new_page(width=200, height=300)
        page.insert_text((20, 40), f"Page {i + 1}")
    path = tmp_path / "sample.pdf"
    doc.save(path)
    doc.close()
    return str(path)


@pytest.fixture
def reader(clock, pdf_path):
    r = PDFReader(clock=clock)
    assert r.load_pdf(pdf_path)
    yield r
    r.close()


def test_load_counts_first_page_as_read(reader):
    stats = reader.get_reading_statistics()
    assert stats['total_pages'] == 3
    assert stats['pages_read'] == 1
    assert stats['current_page'] == 1


def test_navigation_bounds(reader):
    assert not reader.previous_page()
    assert reader.next_page() and reader.next_page()
    assert not reader.next_page()
    assert reader.current_page == 2
    assert reader.get_reading_statistics()['pages_read'] == 3


def test_time_per_page(reader, clock):
    clock.advance(10)
    reader.next_page()
    clock.advance(4)
    reader.previous_page()
    assert reader.page_read_times == {0: 10, 1: 4}


def test_zoom_is_clamped():
    r = PDFReader()
    r.set_zoom(10)
    assert r.zoom_level == PDF_CONFIG['max_zoom']
    r.set_zoom(0.01)
    assert r.zoom_level == PDF_CONFIG['min_zoom']


@pytest.mark.parametrize("zoom", [0.5, 1.0, 1.37])
def test_page_image_shape(reader, zoom):
    img = reader.get_current_page_image(zoom=zoom)
    assert img.ndim == 3 and img.shape[2] == 3
    assert img.flags['C_CONTIGUOUS']


def test_invalid_file_keeps_previous_document(reader, tmp_path):
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"not a pdf")
    assert not reader.load_pdf(str(bad))
    assert reader.last_error
    assert reader.document is not None
    assert reader.total_pages == 3
