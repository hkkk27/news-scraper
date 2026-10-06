import pytest

from tracker.bot import Bot, Card, card_keyboard
from tracker.db import connect, kv_get
from tracker.rssfile import read_feed
from tracker.urls import canonical_url, item_key

ALLOWED = 111


class FakeTelegram:
    def __init__(self, updates=None):
        self.updates = updates or []
        self.sent, self.answered, self.edited = [], [], []
        self._next_id = 500

    def get_updates(self, offset=None, timeout=0):
        return [u for u in self.updates if offset is None or u["update_id"] >= offset]

    def send_message(self, chat_id, text, reply_markup=None, disable_preview=True):
        self._next_id += 1
        self.sent.append((chat_id, text, reply_markup))
        return {"message_id": self._next_id}

    def send_document(self, chat_id, path, caption="", file_id=None):
        if chat_id in getattr(self, "blocked", ()):
            raise RuntimeError("sendDocument: Forbidden: bot was blocked by the user")
        self.documents = getattr(self, "documents", []) + [(chat_id, str(path), file_id)]
        return {"message_id": 1, "document": {"file_id": "FILE-1"}}

    def answer_callback(self, callback_id, text=""):
        self.answered.append((callback_id, text))

    def edit_reply_markup(self, chat_id, message_id, reply_markup):
        self.edited.append((chat_id, message_id, reply_markup))

    def download_file(self, file_id, max_bytes=0):
        raise RuntimeError("no files in tests")


class FakeHTTP:
    def get(self, url):
        class R:
            text = '<html><head><meta property="og:title" content="Karnataka HC stays fee hike order"></head></html>'
        return R()


@pytest.fixture
def setup(tmp_path):
    conn = connect(tmp_path / "t.db")
    tg = FakeTelegram()
    bot = Bot(tg, conn, [ALLOWED], http=FakeHTTP(), manual_feed=tmp_path / "manual.xml")
    return bot, tg, conn, tmp_path


def msg(update_id, text, chat=ALLOWED, **extra):
    return {"update_id": update_id, "message": {"message_id": update_id, "date": 1790500000,
                                                "chat": {"id": chat}, "from": {"id": 7, "first_name": "Sid"},
                                                "text": text, **extra}}


def test_canonical_url_and_key_are_stable():
    a = canonical_url("https://www.example.com/news/x/?utm_source=tw&id=5#top")
    assert a == "https://example.com/news/x?id=5"
    assert item_key("https://m.example.com/news/x/amp") == item_key("https://example.com/news/x")


def test_unknown_chat_gets_its_id_only(setup):
    bot, tg, conn, _ = setup
    assert bot.handle_update(msg(1, "/start", chat=999)) == "ignored"
    assert "999" in tg.sent[0][1]
    assert bot.handle_update(msg(2, "https://x.in/a", chat=999)) == "ignored"
    assert len(tg.sent) == 1


def test_card_buttons_record_feedback_and_mute(setup):
    bot, tg, conn, _ = setup
    card = Card(url="https://example.com/a", title="UGC notifies rules", feed_id="gn-higher-en")
    bot.send_cards(ALLOWED, [card])
    assert card_keyboard(card.key)["inline_keyboard"][0][0]["callback_data"] == f"fb:r:{card.key}"
    for code in ("r", "m"):
        update = {"update_id": 10, "callback_query": {"id": "cb", "data": f"fb:{code}:{card.key}", "from": {"id": 7},
                                                      "message": {"message_id": 501, "chat": {"id": ALLOWED}}}}
        assert bot.handle_update(update) == "feedback"
    rows = conn.execute("SELECT label, value, url, feed_id FROM feedback ORDER BY id").fetchall()
    assert [(r["label"], r["value"]) for r in rows] == [("relevant", 1), ("mute_source", None)]
    assert rows[0]["url"] == "https://example.com/a"
    assert conn.execute("SELECT feed_id FROM muted_sources").fetchone()["feed_id"] == "gn-higher-en"
    assert tg.answered and tg.edited


def test_forwarded_link_becomes_manual_item_and_positive_label(setup):
    bot, tg, conn, tmp = setup
    assert bot.handle_update(msg(3, "see this https://www.livelaw.in/x?utm_source=wa")) == "intake"
    items = read_feed(tmp / "manual.xml")
    assert items[0].title == "Karnataka HC stays fee hike order"
    assert items[0].link == "https://livelaw.in/x"
    fb = conn.execute("SELECT label, value, source FROM feedback").fetchone()
    assert (fb["label"], fb["value"], fb["source"]) == ("manual", 1, "manual")
    assert "Added" in tg.sent[-1][1]


def test_plain_text_intake_and_poll_offset(setup):
    bot, tg, conn, tmp = setup
    tg.updates = [msg(20, "Rajasthan transfers 14 IAS officers\nFull list attached in the order"), msg(21, "/help")]
    stats = bot.poll_once()
    assert stats["intake"] == 1 and stats["command"] == 1
    assert kv_get(conn, "telegram_offset") == "21"
    assert read_feed(tmp / "manual.xml")[0].title == "Rajasthan transfers 14 IAS officers"


def test_registered_command_returns_cards(setup):
    bot, tg, conn, _ = setup
    bot.commands["/search"] = lambda q: [Card(url="https://e.com/1", title=f"Result for {q}")]
    bot.handle_update(msg(30, "/search NEET"))
    assert tg.sent[-1][1].startswith("<b>Result for NEET</b>")


# --- public mode: anyone can subscribe and read; only admins train and add items ---------------

@pytest.fixture
def public(tmp_path):
    conn = connect(tmp_path / "t.db")
    tg = FakeTelegram()
    bot = Bot(tg, conn, [ALLOWED], http=FakeHTTP(), manual_feed=tmp_path / "manual.xml", public=True)
    bot.commands["/today"] = lambda _: [Card(url=f"https://e.com/{n}", title=f"Story {n}") for n in range(5)]
    return bot, tg, conn, tmp_path


def test_public_user_can_subscribe_read_and_stop(public):
    bot, tg, conn, _ = public
    assert bot.handle_update(msg(1, "/start", chat=999)) == "command"
    assert "daily brief" in tg.sent[-1][1] and bot.subscribers() == [999]
    bot.handle_update(msg(2, "/today", chat=999))
    lists = tg.sent[1:]
    assert len(lists) == 2 and all(markup is None for _, _, markup in lists)      # 5 stories, 4 per message
    assert conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0] == 0          # nothing to press later
    bot.handle_update(msg(3, "/stop", chat=999))
    assert bot.subscribers() == []
    bot.handle_update(msg(4, "/start", chat=999))
    assert bot.subscribers() == [999]


def test_public_user_cannot_add_items_or_train(public):
    bot, tg, conn, tmp = public
    assert bot.handle_update(msg(5, "https://x.in/a", chat=999)) == "ignored"
    assert "admins" in tg.sent[-1][1] and not (tmp / "manual.xml").exists()
    press = {"update_id": 6, "callback_query": {"id": "cb", "data": "fb:n:abc", "from": {"id": 9},
                                                "message": {"message_id": 1, "chat": {"id": 999}}}}
    assert bot.handle_update(press) == "ignored"
    bot.handle_update(msg(7, "/users", chat=999))
    assert "Unknown command" in tg.sent[-1][1]
    assert conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0] == 0


def test_brief_goes_to_admins_and_subscribers_and_survives_a_blocked_chat(public):
    bot, tg, conn, tmp = public
    for update_id, chat in ((10, 999), (11, 888)):
        bot.handle_update(msg(update_id, "/start", chat=chat))
    tg.blocked = {999}
    cards = [Card(url="https://e.com/a", title="UGC notifies rules")]
    assert bot.recipients() == [ALLOWED, 888, 999]
    assert bot.broadcast([(tmp / "brief.pdf", "Daily brief")], cards) == 2
    assert [(chat, file_id) for chat, _, file_id in tg.documents] == [(ALLOWED, None), (888, "FILE-1")]
    assert [chat for chat, _, markup in tg.sent if markup] == [ALLOWED]             # buttons for the admin only
    assert bot.subscribers() == [888]                                               # the blocked chat is dropped
    bot.handle_update(msg(12, "/users"))
    assert "1 public subscriber" in tg.sent[-1][1]


def test_private_mode_sends_the_brief_to_admins_only(setup):
    bot, tg, conn, tmp = setup
    bot._subscribe(999, True)
    assert bot.recipients() == [ALLOWED]
