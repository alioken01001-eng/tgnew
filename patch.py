#!/usr/bin/env python3
"""
Telegram-Android fork patcher.

Resmiy Telegram manba kodiga (DrKLO/Telegram) o'zgartirishlar kiritadi:
  1) Brending: paket nomi, ilova nomi, o'z api_id/api_hash
  2) Tozalash: Telegram'ning yangilanish tekshiruvi, passkey, billing o'chiriladi
  3) Funksiyalar (FEATURES orqali): ghost_read, no_typing, ghost_stories, hide_online, more_accounts

Dizayn, animatsiya, ekranlar: HECH QANDAY o'zgartirilmaydi (Telegram'nikidek qoladi).
Har bir patch aynan 1 ta moslik topmasa, aniq xabar bilan to'xtaydi.
"""
import os, re, sys, json, pathlib

SRC = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "tg").resolve()
env = os.environ.get

API_ID = env("TG_API_ID", "").strip()
API_HASH = env("TG_API_HASH", "").strip()
PACKAGE = env("APP_PACKAGE", "").strip()
APP_NAME = env("APP_NAME", "").strip()
FEATURES = {f.strip() for f in env("FEATURES", "").split(",") if f.strip()}
GSERVICES = env("GOOGLE_SERVICES_JSON", "").strip()

JAVA = SRC / "TMessagesProj/src/main/java/org/telegram"


def read(p):
    return pathlib.Path(p).read_text(encoding="utf-8")


def write(p, s):
    pathlib.Path(p).write_text(s, encoding="utf-8")


def replace_once(path, old, new, label):
    s = read(path)
    n = s.count(old)
    if n != 1:
        sys.exit(f"[XATO] '{label}': {path} ichida {n} ta moslik topildi (1 ta kerak edi). "
                 f"Telegram kodi o'zgargan bo'lishi mumkin: UPSTREAM_SHA ni tekshiring.")
    write(path, s.replace(old, new))
    print(f"[OK] {label}")


# ---------------------------------------------------------------- 1) Brending
def branding():
    if not PACKAGE:
        sys.exit("[XATO] APP_PACKAGE berilmagan (masalan: com.sizning.klon)")
    if not re.fullmatch(r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+", PACKAGE):
        sys.exit("[XATO] APP_PACKAGE noto'g'ri formatda. Masalan: com.sizning.klon")
    if not (API_ID.isdigit() and re.fullmatch(r"[0-9a-f]{32}", API_HASH)):
        sys.exit("[XATO] TG_API_ID (raqam) va TG_API_HASH (32 belgi) kerak: my.telegram.org")

    # paket nomi
    gp = SRC / "gradle.properties"
    replace_once(gp, "APP_PACKAGE=org.telegram.messenger", f"APP_PACKAGE={PACKAGE}", "paket nomi")

    # api_id / api_hash
    bv = JAVA / "messenger/BuildVars.java"
    replace_once(bv, "public static int APP_ID = 4;", f"public static int APP_ID = {API_ID};", "api_id")
    replace_once(bv, 'public static String APP_HASH = "014b35b6184100b085b0d0572f9b5103";',
                 f'public static String APP_HASH = "{API_HASH}";', "api_hash")

    # Telegram'ga xos narsalarni o'chirish (forkda ishlamaydi yoki xavfli)
    replace_once(bv, "public static boolean CHECK_UPDATES = true;",
                 "public static boolean CHECK_UPDATES = false;", "yangilanish tekshiruvi o'chirildi")
    replace_once(bv, "public static boolean SUPPORTS_PASSKEYS = true;",
                 "public static boolean SUPPORTS_PASSKEYS = false;", "passkey o'chirildi")
    replace_once(bv, "public static boolean IS_BILLING_UNAVAILABLE = false;",
                 "public static boolean IS_BILLING_UNAVAILABLE = true;", "Google billing o'chirildi")

    # ilova nomi (asosiy strings.xml)
    if APP_NAME:
        sx = SRC / "TMessagesProj/src/main/res/values/strings.xml"
        replace_once(sx, '<string name="AppName">Telegram</string>',
                     f'<string name="AppName">{APP_NAME}</string>', "ilova nomi")

    # Firebase: google-services.json paket nomiga mos bo'lishi shart (aks holda build yiqiladi)
    gj = SRC / "TMessagesProj_App/google-services.json"
    if GSERVICES:
        json.loads(GSERVICES)  # yaroqli JSON ekanini tekshirish
        write(gj, GSERVICES)
        print("[OK] o'z google-services.json ishlatildi (push ishlaydi)")
    else:
        s = read(gj)
        s = s.replace('"package_name": "org.telegram.messenger', f'"package_name": "{PACKAGE}')
        write(gj, s)
        print("[OK] google-services.json paket nomiga moslandi (push bildirishnomalar ISHLAMAYDI: o'z Firebase kerak)")


# ---------------------------------------------------------------- 2) Funksiyalar
RUNTIME_KEYS = ["ghost_read", "no_typing", "ghost_stories", "hide_online"]


def want(name):
    # settings_ui yoqilgan bo'lsa, barcha 'hook'lar kodga kiritiladi (standart holatda o'chiq)
    return name in FEATURES or "settings_ui" in FEATURES


FORK_CONFIG_JAVA = """package org.telegram.messenger;

import android.content.Context;
import android.content.SharedPreferences;

/** Fork funksiyalari. Standart qiymatlar build vaqtida yoziladi, sozlamalar ekrani ularni almashtiradi. */
public class ForkConfig {
    public static boolean GHOST_READ = @GHOST_READ@;
    public static boolean NO_TYPING = @NO_TYPING@;
    public static boolean GHOST_STORIES = @GHOST_STORIES@;
    public static boolean HIDE_ONLINE = @HIDE_ONLINE@;

    static {
        load();
    }

    private static SharedPreferences prefs() {
        Context c = ApplicationLoader.applicationContext;
        return c == null ? null : c.getSharedPreferences("forkconfig", Context.MODE_PRIVATE);
    }

    public static void load() {
        SharedPreferences p = prefs();
        if (p == null) {
            return;
        }
        GHOST_READ = p.getBoolean("ghost_read", GHOST_READ);
        NO_TYPING = p.getBoolean("no_typing", NO_TYPING);
        GHOST_STORIES = p.getBoolean("ghost_stories", GHOST_STORIES);
        HIDE_ONLINE = p.getBoolean("hide_online", HIDE_ONLINE);
    }

    public static boolean get(String key) {
        switch (key) {
            case "ghost_read": return GHOST_READ;
            case "no_typing": return NO_TYPING;
            case "ghost_stories": return GHOST_STORIES;
            case "hide_online": return HIDE_ONLINE;
            default: return false;
        }
    }

    public static void set(String key, boolean value) {
        switch (key) {
            case "ghost_read": GHOST_READ = value; break;
            case "no_typing": NO_TYPING = value; break;
            case "ghost_stories": GHOST_STORIES = value; break;
            case "hide_online": HIDE_ONLINE = value; break;
            default: return;
        }
        SharedPreferences p = prefs();
        if (p != null) {
            p.edit().putBoolean(key, value).apply();
        }
    }
}
"""

# Sozlamalar ekrani: Telegramning ArchiveSettingsActivity tuzilmasi asosida
FORK_SETTINGS_JAVA = """package org.telegram.ui;

import android.content.Context;
import android.text.TextUtils;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import org.telegram.messenger.ForkConfig;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.ActionBar;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.Cells.HeaderCell;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextInfoPrivacyCell;
import org.telegram.ui.Components.LayoutHelper;
import org.telegram.ui.Components.ListView.AdapterWithDiffUtils;
import org.telegram.ui.Components.RecyclerListView;

import java.util.ArrayList;
import java.util.Objects;

public class ForkSettingsActivity extends BaseFragment {

    private RecyclerListView listView;
    private ListAdapter adapter;

    private static final int VIEW_TYPE_HEADER = 0;
    private static final int VIEW_TYPE_CHECK = 1;
    private static final int VIEW_TYPE_SHADOW = 2;

    private final ArrayList<ItemInner> items = new ArrayList<>();

    @Override
    protected boolean useSimpleActionBar() {
        return true;
    }

    @Override
    public View createView(Context context) {
        setHasOwnBackground(true);

        simpleActionBar.setBackButtonImage(R.drawable.ic_ab_back);
        simpleActionBar.setTitle("Fork sozlamalari");
        simpleActionBar.setActionBarMenuOnItemClick(new ActionBar.ActionBarMenuOnItemClick() {
            @Override
            public void onItemClick(int id) {
                if (id == -1) {
                    finishFragment();
                }
            }
        });

        ForkConfig.load();

        fragmentView = new FrameLayout(context);
        FrameLayout frameLayout = (FrameLayout) fragmentView;

        listView = new RecyclerListView(context);
        listView.setSections();
        listView.setLayoutManager(new LinearLayoutManager(context, LinearLayoutManager.VERTICAL, false) {
            @Override
            public boolean supportsPredictiveItemAnimations() {
                return false;
            }
        });
        listView.setVerticalScrollBarEnabled(false);
        listView.setSectionsDrawBackground(true);
        listView.setLayoutAnimation(null);
        listView.setAdapter(adapter = new ListAdapter());
        frameLayout.addView(listView, LayoutHelper.createFrame(LayoutHelper.MATCH_PARENT, LayoutHelper.MATCH_PARENT));
        listView.setOnItemClickListener((view, position) -> {
            if (position < 0 || position >= items.size()) {
                return;
            }
            ItemInner item = items.get(position);
            if (item.key != null && view instanceof TextCheckCell) {
                boolean value = !ForkConfig.get(item.key);
                ForkConfig.set(item.key, value);
                ((TextCheckCell) view).setChecked(value);
            }
        });

        buildItems();
        adapter.notifyDataSetChanged();
        return fragmentView;
    }

    private void buildItems() {
        items.clear();
        items.add(new ItemInner(VIEW_TYPE_HEADER, null, "Maxfiylik (Ghost rejimi)"));
        items.add(new ItemInner(VIEW_TYPE_CHECK, "ghost_read", "O'qilganini bildirmaslik"));
        items.add(new ItemInner(VIEW_TYPE_CHECK, "no_typing", "\\"Yozmoqda...\\" holatini yubormaslik"));
        items.add(new ItemInner(VIEW_TYPE_CHECK, "ghost_stories", "Story ko'rilganini bildirmaslik"));
        items.add(new ItemInner(VIEW_TYPE_CHECK, "hide_online", "Online holatini yashirish"));
        items.add(new ItemInner(VIEW_TYPE_SHADOW, null, "O'zgarishlar darhol kuchga kiradi. Qayta ishga tushirish shart emas."));
    }

    private static class ItemInner extends AdapterWithDiffUtils.Item {
        public final String key;
        public final CharSequence text;

        public ItemInner(int viewType, String key, CharSequence text) {
            super(viewType, false);
            this.key = key;
            this.text = text;
        }

        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (o == null || getClass() != o.getClass()) return false;
            ItemInner item = (ItemInner) o;
            return Objects.equals(key, item.key) && Objects.equals(text, item.text);
        }
    }

    private class ListAdapter extends AdapterWithDiffUtils {
        @NonNull
        @Override
        public RecyclerView.ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
            View view;
            if (viewType == VIEW_TYPE_HEADER) {
                view = new HeaderCell(getContext());
            } else if (viewType == VIEW_TYPE_CHECK) {
                view = new TextCheckCell(getContext());
            } else {
                view = new TextInfoPrivacyCell(getContext());
            }
            return new RecyclerListView.Holder(view);
        }

        @Override
        public void onBindViewHolder(@NonNull RecyclerView.ViewHolder holder, int position) {
            if (position < 0 || position >= items.size()) {
                return;
            }
            ItemInner item = items.get(position);
            final boolean divider = position + 1 < items.size() && items.get(position + 1).viewType == item.viewType;
            if (holder.getItemViewType() == VIEW_TYPE_HEADER) {
                ((HeaderCell) holder.itemView).setText(item.text);
            } else if (holder.getItemViewType() == VIEW_TYPE_SHADOW) {
                TextInfoPrivacyCell cell = (TextInfoPrivacyCell) holder.itemView;
                if (TextUtils.isEmpty(item.text)) {
                    cell.setFixedSize(12);
                    cell.setText(null);
                } else {
                    cell.setFixedSize(0);
                    cell.setText(item.text);
                }
            } else if (holder.getItemViewType() == VIEW_TYPE_CHECK) {
                TextCheckCell cell = (TextCheckCell) holder.itemView;
                cell.setTextAndCheck(item.text, ForkConfig.get(item.key), divider);
            }
        }

        @Override
        public int getItemCount() {
            return items.size();
        }

        @Override
        public boolean isEnabled(RecyclerView.ViewHolder holder) {
            return holder.getItemViewType() == VIEW_TYPE_CHECK;
        }

        @Override
        public int getItemViewType(int position) {
            if (position < 0 || position >= items.size()) {
                return 0;
            }
            return items.get(position).viewType;
        }
    }

    @Nullable
    @Override
    protected RecyclerListView getListViewForSimpleGlass() {
        return listView;
    }

    @Override
    public boolean isSupportEdgeToEdge() {
        return true;
    }
}
"""


def fork_config():
    src = FORK_CONFIG_JAVA
    for k in RUNTIME_KEYS:
        src = src.replace("@" + k.upper() + "@", str(k in FEATURES).lower())
    write(JAVA / "messenger/ForkConfig.java", src)
    print(f"[OK] ForkConfig yaratildi (standart yoqilganlar: {sorted(k for k in RUNTIME_KEYS if k in FEATURES) or 'yoq'})")


def settings_ui():
    write(JAVA / "ui/ForkSettingsActivity.java", FORK_SETTINGS_JAVA)
    pa = JAVA / "ui/ProfileActivity.java"
    replace_once(pa, "    private int liteModeRow;\n",
                 "    private int liteModeRow;\n    private int forkRow;\n", "settings_ui: forkRow maydoni")
    replace_once(pa, "        liteModeRow = -1;\n",
                 "        liteModeRow = -1;\n        forkRow = -1;\n", "settings_ui: forkRow reset")
    replace_once(pa, "                liteModeRow = rowCount++;\n",
                 "                liteModeRow = rowCount++;\n                forkRow = rowCount++;\n", "settings_ui: forkRow qator")
    replace_once(pa, "            } else if (position == liteModeRow) {\n                presentFragment(new LiteModeSettingsActivity());\n",
                 "            } else if (position == forkRow) {\n                presentFragment(new ForkSettingsActivity());\n"
                 "            } else if (position == liteModeRow) {\n                presentFragment(new LiteModeSettingsActivity());\n",
                 "settings_ui: forkRow bosilishi")
    replace_once(pa, "                    } else if (position == liteModeRow) {\n                        textCell.setTextAndIcon(LocaleController.getString(R.string.PowerUsage), R.drawable.msg2_battery, true);\n",
                 "                    } else if (position == forkRow) {\n                        textCell.setTextAndIcon(\"Fork sozlamalari\", R.drawable.msg2_secret, true);\n"
                 "                    } else if (position == liteModeRow) {\n                        textCell.setTextAndIcon(LocaleController.getString(R.string.PowerUsage), R.drawable.msg2_battery, true);\n",
                 "settings_ui: forkRow matni")
    replace_once(pa, "position == businessRow || position == liteModeRow || position == birthdayRow",
                 "position == businessRow || position == liteModeRow || position == forkRow || position == birthdayRow",
                 "settings_ui: isEnabled #1")
    replace_once(pa, "position == addToContactsRow || position == liteModeRow || position == premiumGiftingRow",
                 "position == addToContactsRow || position == liteModeRow || position == forkRow || position == premiumGiftingRow",
                 "settings_ui: isEnabled #2")
    replace_once(pa, "            put(++pointer, liteModeRow, sparseIntArray);\n",
                 "            put(++pointer, liteModeRow, sparseIntArray);\n            put(++pointer, forkRow, sparseIntArray);\n",
                 "settings_ui: sparse tartib")


def features():
    fork_config()
    mc = JAVA / "messenger/MessagesController.java"

    if "settings_ui" in FEATURES:
        settings_ui()

    if want("ghost_read"):
        replace_once(mc, "    private void completeReadTask(ReadTask task) {\n",
                     "    private void completeReadTask(ReadTask task) {\n"
                     "        if (ForkConfig.GHOST_READ) {\n            return;\n        }\n",
                     "ghost_read: o'qildi belgisi yuborilmaydi")

    if want("no_typing"):
        replace_once(mc,
                     "    public boolean sendTyping(long dialogId, long threadMsgId, int action, String emojicon, int classGuid) {\n",
                     "    public boolean sendTyping(long dialogId, long threadMsgId, int action, String emojicon, int classGuid) {\n"
                     "        if (ForkConfig.NO_TYPING) {\n            return false;\n        }\n",
                     "no_typing: yozmoqda holati yuborilmaydi")

    if want("ghost_stories"):
        sc = JAVA / "ui/Stories/StoriesController.java"
        replace_once(sc,
                     "            ConnectionsManager.getInstance(currentAccount).sendRequest(req, (response, error) -> {});\n"
                     "            NotificationCenter.getInstance(currentAccount).postNotificationName(NotificationCenter.storiesReadUpdated);",
                     "            if (!org.telegram.messenger.ForkConfig.GHOST_STORIES) {\n"
                     "                ConnectionsManager.getInstance(currentAccount).sendRequest(req, (response, error) -> {});\n"
                     "            }\n"
                     "            NotificationCenter.getInstance(currentAccount).postNotificationName(NotificationCenter.storiesReadUpdated);",
                     "ghost_stories: story ko'rilgani yuborilmaydi")

    if want("hide_online"):
        replace_once(mc,
                     "            if (!ignoreSetOnline && getConnectionsManager().getPauseTime() == 0 && ApplicationLoader.isScreenOn",
                     "            if (!ignoreSetOnline && !ForkConfig.HIDE_ONLINE && getConnectionsManager().getPauseTime() == 0 && ApplicationLoader.isScreenOn",
                     "hide_online: online holati yuborilmaydi")

    if "more_accounts" in FEATURES:
        # Akkaunt limiti: 3-5 o'rniga 10 (cheklov faqat mijozda, serverda emas)
        uc = JAVA / "messenger/UserConfig.java"
        replace_once(uc, "public final static int MAX_ACCOUNT_DEFAULT_COUNT = 3;",
                     "public final static int MAX_ACCOUNT_DEFAULT_COUNT = 10;", "more_accounts: default 10")
        replace_once(uc, "public final static int MAX_ACCOUNT_COUNT = 4;",
                     "public final static int MAX_ACCOUNT_COUNT = 10;", "more_accounts: max 10")
        replace_once(uc, "return hasPremiumOnAccounts() ? 5 : 3;",
                     "return 10;", "more_accounts: getMaxAccountCount 10")


if __name__ == "__main__":
    print(f"Manba: {SRC}\nFunksiyalar: {sorted(FEATURES) or 'yoq'}")
    branding()
    features()
    print("Patch tugadi.")
