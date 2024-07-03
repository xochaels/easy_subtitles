# conftest.py

def pytest_addoption(parser):
    parser.addoption("--link_sub", action="store", default="", help="Link to subtitles")
    parser.addoption("--from_episode", action="store", type=int, default=1, help="From Episode")
    parser.addoption("--to_episode", action="store", type=int, default=1, help="To Episode")
