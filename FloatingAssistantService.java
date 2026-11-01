package com.nahata.assistant;

import android.app.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.graphics.PixelFormat;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.IBinder;
import android.provider.Settings;
import android.view.*;
import android.view.inputmethod.InputMethodManager;
import android.widget.*;
import android.text.Editable;
import android.text.TextWatcher;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;

public class FloatingAssistantService extends Service {
    private static final String CHANNEL = "nahata_assistant_active";
    private static final String WEBSITE = "https://nahata-ai.onrender.com/";
    private WindowManager wm;
    private View bubble, panel;
    private WindowManager.LayoutParams bubbleLp;
    private boolean panelOpen = false;
    private LinearLayout appRows;
    private EditText appSearch;
    private final List<ResolveInfo> launchableApps = new ArrayList<>();

    @Override public void onCreate() {
        super.onCreate();
        wm = (WindowManager) getSystemService(WINDOW_SERVICE);
        createChannel();
        startForeground(71, notification());
        loadLaunchableApps();
        showBubble();
    }

    @Override public int onStartCommand(Intent i, int flags, int id) {
        if (bubble == null) showBubble();
        return START_STICKY;
    }
    @Override public IBinder onBind(Intent i) { return null; }

    private void createChannel() {
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel c = new NotificationChannel(CHANNEL, "Nahata AI assistant", NotificationManager.IMPORTANCE_LOW);
            c.setDescription("Shown while your user-enabled Nahata AI floating assistant is active.");
            ((NotificationManager) getSystemService(NOTIFICATION_SERVICE)).createNotificationChannel(c);
        }
    }

    private Notification notification() {
        Intent open = new Intent(this, MainActivity.class);
        PendingIntent pi = PendingIntent.getActivity(this, 0, open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder b = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(this, CHANNEL) : new Notification.Builder(this);
        return b.setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentTitle("Nahata AI is ready")
                .setContentText("Tap the N bubble, or long-press it to open the mini panel.")
                .setContentIntent(pi).setOngoing(true).build();
    }

    private GradientDrawable shape(int color, int stroke) {
        GradientDrawable d = new GradientDrawable(); d.setColor(color); d.setCornerRadius(dp(22)); d.setStroke(dp(1), stroke); return d;
    }
    private int dp(int n) { return (int) (n * getResources().getDisplayMetrics().density + .5f); }

    private WindowManager.LayoutParams params(int w, int h, int gravity, boolean focusable) {
        int type = Build.VERSION.SDK_INT >= 26 ? WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY : WindowManager.LayoutParams.TYPE_PHONE;
        int flags = WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN;
        if (!focusable) flags |= WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL;
        else flags |= WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL;
        return new WindowManager.LayoutParams(w, h, type, flags, PixelFormat.TRANSLUCENT, gravity);
    }

    private void showBubble() {
        if (!Settings.canDrawOverlays(this) || bubble != null) return;
        TextView v = new TextView(this);
        v.setText("N"); v.setTextColor(0xFFFFFFFF); v.setTextSize(22); v.setTypeface(Typeface.DEFAULT_BOLD); v.setGravity(Gravity.CENTER);
        v.setBackground(shape(0xEE063B59, 0xFF00D4FF)); v.setElevation(dp(12)); bubble = v;
        bubbleLp = params(dp(58), dp(58), Gravity.RIGHT | Gravity.BOTTOM, false);
        bubbleLp.x = dp(12); bubbleLp.y = dp(120);
        final float[] down = {0, 0}; final long[] when = {0}; final boolean[] moved = {false};
        v.setOnTouchListener((view, event) -> {
            switch (event.getAction()) {
                case MotionEvent.ACTION_DOWN:
                    down[0] = event.getRawX(); down[1] = event.getRawY(); when[0] = System.currentTimeMillis(); moved[0] = false; return true;
                case MotionEvent.ACTION_MOVE:
                    float dx = down[0] - event.getRawX(), dy = down[1] - event.getRawY();
                    if (Math.abs(dx) > dp(5) || Math.abs(dy) > dp(5)) moved[0] = true;
                    if (moved[0]) {
                        bubbleLp.x = Math.max(0, bubbleLp.x + (int) dx);
                        bubbleLp.y = Math.max(0, bubbleLp.y + (int) dy);
                        try { wm.updateViewLayout(bubble, bubbleLp); } catch (Exception ignored) { }
                        down[0] = event.getRawX(); down[1] = event.getRawY();
                    }
                    return true;
                case MotionEvent.ACTION_UP:
                    long held = System.currentTimeMillis() - when[0];
                    if (!moved[0]) { if (held >= 450) togglePanel(); else openWebsite(); }
                    else if (held >= 450) togglePanel();
                    return true;
            }
            return true;
        });
        try { wm.addView(bubble, bubbleLp); } catch (Exception e) { bubble = null; stopSelf(); }
    }

    private TextView label(String text, int size, int color) {
        TextView t = new TextView(this); t.setText(text); t.setTextSize(size); t.setTextColor(color); return t;
    }
    private Button button(String text, Runnable run) {
        Button b = new Button(this); b.setText(text); b.setAllCaps(false); b.setTextColor(0xFFFFFFFF);
        b.setBackgroundTintList(android.content.res.ColorStateList.valueOf(0xFF075A75)); b.setOnClickListener(v -> run.run()); return b;
    }

    private void loadLaunchableApps() {
        launchableApps.clear();
        Intent query = new Intent(Intent.ACTION_MAIN, null); query.addCategory(Intent.CATEGORY_LAUNCHER);
        PackageManager pm = getPackageManager();
        List<ResolveInfo> found;
        if (Build.VERSION.SDK_INT >= 33) found = pm.queryIntentActivities(query, PackageManager.ResolveInfoFlags.of(0));
        else found = pm.queryIntentActivities(query, 0);
        launchableApps.addAll(found);
        Collections.sort(launchableApps, (a, b) -> String.CASE_INSENSITIVE_ORDER.compare(
                String.valueOf(a.loadLabel(pm)), String.valueOf(b.loadLabel(pm))));
    }

    private void togglePanel() { if (panelOpen) closePanel(); else openPanel(); }

    private void openPanel() {
        if (!Settings.canDrawOverlays(this) || panelOpen) return;
        LinearLayout box = new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(14), dp(12), dp(14), dp(12)); box.setBackground(shape(0xF5091423, 0xFF00D4FF));
        LinearLayout head = new LinearLayout(this); head.setGravity(Gravity.CENTER_VERTICAL);
        TextView title = label("NAHATA AI MINI", 15, 0xFF00D4FF); title.setTypeface(Typeface.DEFAULT_BOLD);
        head.addView(title, new LinearLayout.LayoutParams(0, -2, 1)); head.addView(button("✕", this::closePanel)); box.addView(head);
        TextView sub = label("JARVIS  •  ULTRON  •  PHONE APP LAUNCHER", 10, 0xFFB7D8E5); sub.setPadding(0, dp(5), 0, dp(8)); box.addView(sub);
        LinearLayout modes = new LinearLayout(this); modes.setOrientation(LinearLayout.HORIZONTAL);
        modes.addView(button("JARVIS", this::openWebsite), new LinearLayout.LayoutParams(0, dp(44), 1));
        modes.addView(button("ULTRON", this::openWebsite), new LinearLayout.LayoutParams(0, dp(44), 1)); box.addView(modes);
        box.addView(button("OPEN NAHATA AI CHAT", this::openWebsite));
        box.addView(button("🎙 SAY AN APP NAME", this::startVoiceAppCommand));
        TextView all = label("Find and open installed apps", 13, 0xFFE6F7FF); all.setPadding(0, dp(8), 0, dp(4)); box.addView(all);
        appSearch = new EditText(this); appSearch.setSingleLine(true); appSearch.setTextColor(0xFFFFFFFF); appSearch.setHintTextColor(0xFF8CA9B8);
        appSearch.setHint("Search an installed app…"); appSearch.setTextSize(14); appSearch.setPadding(dp(10), dp(8), dp(10), dp(8));
        appSearch.setBackground(shape(0xFF102435, 0xFF23627A)); box.addView(appSearch);
        ScrollView scroll = new ScrollView(this); appRows = new LinearLayout(this); appRows.setOrientation(LinearLayout.VERTICAL); scroll.addView(appRows);
        LinearLayout.LayoutParams slp = new LinearLayout.LayoutParams(-1, dp(230)); slp.topMargin = dp(6); box.addView(scroll, slp);
        appSearch.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int st, int c, int a) { }
            @Override public void onTextChanged(CharSequence s, int st, int before, int count) { renderApps(s.toString()); }
            @Override public void afterTextChanged(Editable e) { }
        });
        renderApps("");
        TextView foot = label("Offline: the panel and launchable app list work without mobile data. Online AI chat needs internet. Android hides some protected or non-launchable apps.", 10, 0xFF8CA9B8);
        foot.setPadding(0, dp(7), 0, 0); box.addView(foot);
        panel = box;
        WindowManager.LayoutParams lp = params(Math.min(getResources().getDisplayMetrics().widthPixels - dp(20), dp(380)), WindowManager.LayoutParams.WRAP_CONTENT, Gravity.BOTTOM | Gravity.CENTER_HORIZONTAL, true);
        lp.y = dp(82); lp.softInputMode = WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE;
        try { wm.addView(panel, lp); panelOpen = true; }
        catch (Exception e) { panel = null; panelOpen = false; }
    }

    private void renderApps(String filter) {
        if (appRows == null) return;
        appRows.removeAllViews(); String q = filter == null ? "" : filter.trim().toLowerCase(Locale.ROOT);
        PackageManager pm = getPackageManager(); int shown = 0;
        for (ResolveInfo ri : launchableApps) {
            String label = String.valueOf(ri.loadLabel(pm));
            if (!q.isEmpty() && !label.toLowerCase(Locale.ROOT).contains(q)) continue;
            String pkg = ri.activityInfo.packageName;
            Button b = button("▸  " + label, () -> launchPackage(pkg));
            LinearLayout.LayoutParams bp = new LinearLayout.LayoutParams(-1, dp(42)); bp.topMargin = dp(3); appRows.addView(b, bp);
            shown++; if (shown >= 60 && q.isEmpty()) break;
        }
        if (shown == 0) { TextView none = label("No launchable app found for that name.", 12, 0xFFB7D8E5); none.setPadding(dp(6), dp(10), dp(6), dp(10)); appRows.addView(none); }
        if (q.isEmpty() && launchableApps.size() > shown) {
            TextView hint = label("Showing first " + shown + " apps. Search to find another.", 10, 0xFF8CA9B8); hint.setPadding(dp(6), dp(6), dp(6), dp(6)); appRows.addView(hint);
        }
    }

    private void launchPackage(String pkg) {
        try {
            Intent i = getPackageManager().getLaunchIntentForPackage(pkg);
            if (i == null) { Toast.makeText(this, "Android does not expose a launch screen for this app.", Toast.LENGTH_SHORT).show(); return; }
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK); startActivity(i);
        } catch (Exception e) { Toast.makeText(this, "Could not open this app on this phone.", Toast.LENGTH_SHORT).show(); }
    }
    private void openWebsite() {
        try { Intent i = new Intent(Intent.ACTION_VIEW, Uri.parse(WEBSITE)); i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK); startActivity(i); }
        catch (Exception e) { Toast.makeText(this, "Nahata AI website could not be opened.", Toast.LENGTH_SHORT).show(); }
    }
    private void startVoiceAppCommand() {
        try {
            Intent i = new Intent(this, MainActivity.class);
            i.putExtra("voice_app_command", true);
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
            startActivity(i);
        } catch (Exception e) { Toast.makeText(this, "Voice command could not be started.", Toast.LENGTH_SHORT).show(); }
    }
    private void closePanel() {
        if (panel != null) { try { wm.removeView(panel); } catch (Exception ignored) { } panel = null; }
        panelOpen = false; appRows = null; appSearch = null;
    }
    @Override public void onDestroy() {
        closePanel();
        if (bubble != null) { try { wm.removeView(bubble); } catch (Exception ignored) { } bubble = null; }
        super.onDestroy();
    }
}
