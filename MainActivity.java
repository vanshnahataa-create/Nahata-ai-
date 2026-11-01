package com.nahata.assistant;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.speech.RecognizerIntent;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {
    private static final int REQ_NOTIF = 40;
    private static final int REQ_MIC = 41;
    private static final int REQ_VOICE = 42;
    private LinearLayout root;
    private TextView status;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(0xFF030B14);
        getWindow().setNavigationBarColor(0xFF030B14);
        buildUi();
        if (getIntent() != null && getIntent().getBooleanExtra("show_mini", false)) startIfAllowed();
        if (getIntent() != null && getIntent().getBooleanExtra("voice_app_command", false)) startVoiceAppCommand();
    }

    private void buildUi() {
        root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(24, 38, 24, 24); root.setBackgroundColor(0xFF030B14);
        TextView title = new TextView(this); title.setText("NAHATA AI"); title.setTextColor(0xFF00D4FF); title.setTextSize(26); title.setGravity(Gravity.CENTER); title.setLetterSpacing(.12f);
        root.addView(title, new LinearLayout.LayoutParams(-1, 70));
        TextView sub = new TextView(this); sub.setText("JARVIS  •  ULTRON  •  MINI ASSISTANT"); sub.setTextColor(0xFFB7D8E5); sub.setTextSize(12); sub.setGravity(Gravity.CENTER);
        root.addView(sub, new LinearLayout.LayoutParams(-1, 42));
        status = new TextView(this); status.setText("Setup required: allow display over other apps, then enable the floating bubble."); status.setTextColor(0xFFE6F7FF); status.setTextSize(15); status.setPadding(8,24,8,24);
        root.addView(status);
        addButton("1. Allow display over other apps", v -> requestOverlay());
        addButton("2. Start floating assistant", v -> startIfAllowed());
        addButton("Open Nahata AI website", v -> { Intent i=new Intent(Intent.ACTION_VIEW, Uri.parse("https://nahata-ai.onrender.com/")); startActivity(i); });
        addButton("Stop floating assistant", v -> { stopService(new Intent(this, FloatingAssistantService.class)); status.setText("Floating assistant stopped."); });
        TextView note = new TextView(this); note.setText("The small N bubble stays at the bottom-right over other apps. Long-press the bubble to open the mini panel. The app launcher and voice app search work offline; online AI conversations need internet. Android may hide protected or non-launchable apps and may limit background services to save battery."); note.setTextColor(0xFF8CA9B8); note.setTextSize(12); note.setPadding(4,24,4,4); root.addView(note);
        setContentView(root);
    }
    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent); setIntent(intent);
        if (intent != null && intent.getBooleanExtra("voice_app_command", false)) startVoiceAppCommand();
    }

    private void startVoiceAppCommand() {
        if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, REQ_MIC); return;
        }
        Intent speech = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        speech.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        speech.putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault());
        speech.putExtra(RecognizerIntent.EXTRA_PROMPT, "Say: open followed by an app name");
        try { startActivityForResult(speech, REQ_VOICE); }
        catch (Exception e) { Toast.makeText(this, "No speech recognition service is available on this phone.", Toast.LENGTH_LONG).show(); }
    }

    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQ_MIC && grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) startVoiceAppCommand();
        else if (requestCode == REQ_MIC) Toast.makeText(this, "Microphone permission is needed for voice app commands.", Toast.LENGTH_LONG).show();
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != REQ_VOICE || resultCode != RESULT_OK || data == null) return;
        ArrayList<String> results = data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);
        if (results == null || results.isEmpty()) return;
        String spoken = results.get(0).toLowerCase(Locale.ROOT).trim().replaceFirst("^(please\\s+)?(open|launch|start)\\s+", "");
        openMatchingApp(spoken);
    }

    private void openMatchingApp(String requested) {
        Intent query = new Intent(Intent.ACTION_MAIN, null); query.addCategory(Intent.CATEGORY_LAUNCHER);
        List<ResolveInfo> apps;
        if (Build.VERSION.SDK_INT >= 33) apps = getPackageManager().queryIntentActivities(query, PackageManager.ResolveInfoFlags.of(0));
        else apps = getPackageManager().queryIntentActivities(query, 0);
        List<ResolveInfo> matches = new ArrayList<>();
        for (ResolveInfo ri : apps) {
            String label = String.valueOf(ri.loadLabel(getPackageManager())).toLowerCase(Locale.ROOT);
            if (label.equals(requested) || label.contains(requested) || requested.contains(label)) matches.add(ri);
        }
        if (matches.isEmpty()) { Toast.makeText(this, "No launchable app matched: " + requested, Toast.LENGTH_LONG).show(); return; }
        if (matches.size() == 1) { launch(matches.get(0)); return; }
        String[] labels = new String[matches.size()];
        for (int i = 0; i < matches.size(); i++) labels[i] = String.valueOf(matches.get(i).loadLabel(getPackageManager()));
        new AlertDialog.Builder(this).setTitle("Choose an app").setItems(labels, (dialog, which) -> launch(matches.get(which))).show();
    }

    private void launch(ResolveInfo ri) {
        try {
            Intent launch = getPackageManager().getLaunchIntentForPackage(ri.activityInfo.packageName);
            if (launch == null) { Toast.makeText(this, "Android does not expose a launch screen for this app.", Toast.LENGTH_SHORT).show(); return; }
            startActivity(launch);
        } catch (Exception e) { Toast.makeText(this, "Could not open this app.", Toast.LENGTH_SHORT).show(); }
    }

    private void addButton(String label, View.OnClickListener click) {
        Button b=new Button(this); b.setText(label); b.setAllCaps(false); b.setTextColor(0xFFFFFFFF); b.setBackgroundTintList(android.content.res.ColorStateList.valueOf(0xFF075A75));
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1, -2); lp.setMargins(0,8,0,8); root.addView(b,lp); b.setOnClickListener(click);
    }
    private void requestOverlay() {
        if (Build.VERSION.SDK_INT >= 23 && !Settings.canDrawOverlays(this)) {
            Intent i=new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:"+getPackageName())); startActivity(i);
        } else status.setText("Overlay permission is already enabled.");
    }
    private void startIfAllowed() {
        if (Build.VERSION.SDK_INT >= 23 && !Settings.canDrawOverlays(this)) {
            new AlertDialog.Builder(this).setTitle("Permission needed").setMessage("Allow Nahata AI Companion to display a small floating bubble over other apps. You can turn this off anytime in Android Settings.").setPositiveButton("Continue", (d,w)->requestOverlay()).setNegativeButton("Cancel",null).show(); return;
        }
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, REQ_NOTIF);
        }
        Intent i=new Intent(this, FloatingAssistantService.class);
        if (Build.VERSION.SDK_INT >= 26) startForegroundService(i); else startService(i);
        status.setText("Nahata AI floating bubble is active. Long-press the N bubble at the bottom-right.");
        Toast.makeText(this,"Nahata AI assistant started",Toast.LENGTH_SHORT).show();
    }
}
