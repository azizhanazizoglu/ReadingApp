from backend.components.navigator import Navigator


def test_lovable_menu_and_yeni_trafik_full_snippets():
    html = (
        '<button data-lov-name="Button" class="inline-flex">'
        '<svg class="lucide lucide-menu" data-lov-name="Menu"></svg>'
        '</button>'
        '<div class="side-panel open">'
        '<button class="flex items-center"><span>Yeni Trafik</span></button>'
        '</div>'
    )
    nav = Navigator()
    menu = nav.navigator_open_menu_candidates(html)
    task = nav.navigator_go_to_task_candidates("Yeni Trafik", html)
    assert any("menu" in a.description.lower() for a in menu.candidates)
    assert any("Yeni Trafik" in a.description for a in task.candidates)