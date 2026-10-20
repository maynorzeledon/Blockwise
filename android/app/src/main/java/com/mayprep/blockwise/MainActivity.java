package com.mayprep.blockwise;
import android.view.*;import android.widget.FrameLayout;import android.graphics.Color;import androidx.core.graphics.Insets;import androidx.core.view.ViewCompat;import androidx.core.view.WindowCompat;import androidx.core.view.WindowInsetsCompat;import android.app.*;import android.os.*;import android.webkit.*;import android.content.*;import android.net.Uri;import android.provider.MediaStore;import android.speech.tts.TextToSpeech;import java.util.*;import java.io.*;
public class MainActivity extends Activity {
 FrameLayout viewport; WebView web; ValueCallback<Uri[]> chooser; TextToSpeech tts;
 @Override public void onCreate(Bundle state){super.onCreate(state);// The container, not WebView padding, defines the real HTML viewport.
 WindowCompat.setDecorFitsSystemWindows(getWindow(),false);
 getWindow().setStatusBarColor(Color.TRANSPARENT);getWindow().setNavigationBarColor(Color.TRANSPARENT);
 if(Build.VERSION.SDK_INT>=29)getWindow().setNavigationBarContrastEnforced(false);
 viewport=new FrameLayout(this);viewport.setClipToPadding(true);
 web=new WebView(this);web.setId(View.generateViewId());
 web.getSettings().setJavaScriptEnabled(true);web.getSettings().setDomStorageEnabled(true);
 web.getSettings().setAllowFileAccess(false);web.getSettings().setAllowContentAccess(true);
 web.getSettings().setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
 viewport.addView(web,new FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT,FrameLayout.LayoutParams.MATCH_PARENT));
 ViewCompat.setOnApplyWindowInsetsListener(viewport,(view,windowInsets)->{
  int handled=WindowInsetsCompat.Type.systemBars()|WindowInsetsCompat.Type.displayCutout()|WindowInsetsCompat.Type.ime();
  Insets safe=windowInsets.getInsets(handled);
  view.setPadding(safe.left,safe.top,safe.right,safe.bottom);
  // Forward zeroed handled insets so Chromium does not apply them a second time.
  // Unlike CONSUMED, a fresh object still delivers keyboard-hide/rotation updates.
  return new WindowInsetsCompat.Builder(windowInsets).setInsets(handled,Insets.NONE).build();
 });
 setContentView(viewport);setChromeDark((getResources().getConfiguration().uiMode & android.content.res.Configuration.UI_MODE_NIGHT_MASK)==android.content.res.Configuration.UI_MODE_NIGHT_YES);
 viewport.post(()->ViewCompat.requestApplyInsets(viewport));
 web.addJavascriptInterface(new Bridge(),"BlockwiseNative");tts=new TextToSpeech(this,status->{});
 web.setWebViewClient(new WebViewClient(){@Override public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest r){Uri u=r.getUrl();if(u.toString().startsWith("https://blockwise.local/")&&u.getFragment()!=null)return false;if("https".equals(u.getScheme())){try{startActivity(new Intent(Intent.ACTION_VIEW,u));}catch(Exception ignored){}}return true;}@Override public WebResourceResponse shouldInterceptRequest(WebView v,WebResourceRequest r){if(r.getUrl().getHost()!=null&&r.getUrl().getHost().equals("blockwise.local")&&!r.getUrl().getPath().startsWith("/api/")){try{String path=r.getUrl().getPath();if(path.equals("/"))path="index.html";else path=path.substring(1);String mime=path.endsWith(".js")?"text/javascript":path.endsWith(".css")?"text/css":path.endsWith(".json")?"application/json":path.endsWith(".png")?"image/png":path.endsWith(".webp")?"image/webp":path.endsWith(".jpg")?"image/jpeg":path.endsWith(".svg")?"image/svg+xml":"text/html";return new WebResourceResponse(mime,"UTF-8",getAssets().open(path));}catch(Exception e){return new WebResourceResponse("text/plain","UTF-8",404,"Not found",null,new ByteArrayInputStream(new byte[0]));}}return null;}});
 web.setWebChromeClient(new WebChromeClient(){@Override public boolean onShowFileChooser(WebView v,ValueCallback<Uri[]> cb,FileChooserParams p){if(chooser!=null)chooser.onReceiveValue(null);chooser=cb;Intent i=p.createIntent();i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);try{startActivityForResult(i,44);}catch(Exception e){chooser.onReceiveValue(null);chooser=null;}return true;}});
 web.loadUrl("https://blockwise.local/"); }
 @Override protected void onActivityResult(int req,int result,Intent data){super.onActivityResult(req,result,data);if(req==44&&chooser!=null){chooser.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(result,data));chooser=null;}}
 @Override public void onBackPressed(){web.evaluateJavascript("if(document.querySelector('dialog')?.open)document.querySelector('dialog').close();else document.querySelector('[data-page=home]')?.click();",null);}
 @Override protected void onDestroy(){if(tts!=null){tts.stop();tts.shutdown();}web.destroy();super.onDestroy();}
 void setChromeDark(boolean dark){
  int color=Color.parseColor(dark?"#111e19":"#f5f5ed");viewport.setBackgroundColor(color);getWindow().setBackgroundDrawable(new android.graphics.drawable.ColorDrawable(color));
  androidx.core.view.WindowInsetsControllerCompat bars=WindowCompat.getInsetsController(getWindow(),viewport);
  bars.setAppearanceLightStatusBars(!dark);bars.setAppearanceLightNavigationBars(!dark);
 }
 public class Bridge {
  @JavascriptInterface public void setChromeDark(boolean dark){runOnUiThread(()->MainActivity.this.setChromeDark(dark));}
  @JavascriptInterface public boolean isSystemDark(){return (getResources().getConfiguration().uiMode & android.content.res.Configuration.UI_MODE_NIGHT_MASK)==android.content.res.Configuration.UI_MODE_NIGHT_YES;}
  @JavascriptInterface public void exportBackup(String text){if(text.length()>1048576)return;runOnUiThread(()->{try{if(Build.VERSION.SDK_INT>=29){ContentValues cv=new ContentValues();cv.put(MediaStore.Downloads.DISPLAY_NAME,"blockwise-backup-"+System.currentTimeMillis()+".json");cv.put(MediaStore.Downloads.MIME_TYPE,"application/json");Uri u=getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI,cv);try(OutputStream out=getContentResolver().openOutputStream(u)){out.write(text.getBytes("UTF-8"));}android.widget.Toast.makeText(MainActivity.this,"Saved in Downloads / Guardado en Descargas",0).show();}else{Intent i=new Intent(Intent.ACTION_SEND);i.setType("text/plain");i.putExtra(Intent.EXTRA_TEXT,text);startActivity(Intent.createChooser(i,"Save backup / Guardar copia"));}}catch(Exception e){android.widget.Toast.makeText(MainActivity.this,"Could not save / No se pudo guardar",0).show();}});}
  @JavascriptInterface public void exportCatalog(String text,String format){if(text.length()>16777216||(!format.equals("csv")&&!format.equals("json")))return;runOnUiThread(()->{try{if(Build.VERSION.SDK_INT>=29){ContentValues cv=new ContentValues();cv.put(MediaStore.Downloads.DISPLAY_NAME,"blockwise-facts-"+System.currentTimeMillis()+"."+format);cv.put(MediaStore.Downloads.MIME_TYPE,format.equals("csv")?"text/csv":"application/json");Uri u=getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI,cv);try(OutputStream out=getContentResolver().openOutputStream(u)){out.write(text.getBytes("UTF-8"));}android.widget.Toast.makeText(MainActivity.this,"Saved in Downloads / Guardado en Descargas",0).show();}else{Intent i=new Intent(Intent.ACTION_SEND);i.setType("text/plain");i.putExtra(Intent.EXTRA_TEXT,text);startActivity(Intent.createChooser(i,"Export facts / Exportar datos"));}}catch(Exception e){android.widget.Toast.makeText(MainActivity.this,"Could not save / No se pudo guardar",0).show();}});}
  @JavascriptInterface public void share(String text){runOnUiThread(()->{Intent i=new Intent(Intent.ACTION_SEND);i.setType("text/plain");i.putExtra(Intent.EXTRA_TEXT,text);startActivity(Intent.createChooser(i,"Share / Compartir"));});}
  @JavascriptInterface public void speak(String text,String lang){runOnUiThread(()->{int result=tts.setLanguage(lang.equals("es")?new Locale("es"):Locale.US);if(result<0){android.widget.Toast.makeText(MainActivity.this,"Install a voice for this language / Instala una voz para este idioma",0).show();return;}tts.speak(text,TextToSpeech.QUEUE_FLUSH,null,"fact");});}
  @JavascriptInterface public void stop(){tts.stop();}
 }
}
