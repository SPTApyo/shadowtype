from shadowtype import join_art, render_bitmap, render_svg, render_text


def test_render_text_has_shadow_and_equal_lines():
    art = render_text("AB")
    assert "░" in art and not art.endswith("\n\n")
    assert len({len(line) for line in art.splitlines()}) == 1


def test_join_art_inserts_gap():
    joined = join_art("ab\nc\n", "XY\n", 3).splitlines()
    assert joined == ["ab   XY", "c      "]


def test_render_svg_one_tspan_per_line_and_escapes():
    art = render_text("A<&", font="standard")
    svg = render_svg(art, ["#000", "#fff"])
    assert svg.count("<tspan") == len(art.splitlines())
    assert "&lt;" in svg and 'offset="100%"' in svg


def test_render_svg_width_scales_height():
    art = render_text("A")
    native = render_svg(art, ["#000"])
    assert 'height="138"' in native
    scaled = render_svg(art, ["#000"], display_width=2000)
    assert 'width="2000"' in scaled and "viewBox" in scaled


def test_render_bitmap_rows_control_resolution():
    small = render_bitmap("HI", 6).splitlines()
    big = render_bitmap("HI", 20).splitlines()
    assert len(small) <= 7 and len(big) > 15
    assert len(big[0]) > len(small[0])
    assert len({len(line) for line in big}) == 1
    assert "█" in big[5] and "░" in "".join(big)


def test_render_svg_solid_and_direction():
    svg = render_svg(render_text("A"), ["#00ff41"], direction="vertical")
    assert svg.count("<stop") == 1 and 'x2="0%" y2="100%"' in svg
