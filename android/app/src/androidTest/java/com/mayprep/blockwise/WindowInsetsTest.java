package com.mayprep.blockwise;
import android.content.pm.ActivityInfo;
import android.graphics.Bitmap;
import android.graphics.Rect;
import android.os.SystemClock;
import android.view.View;
import android.view.inputmethod.InputMethodManager;
import android.content.Context;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.rule.ActivityTestRule;
import org.junit.Rule;
import org.junit.Test;
import org.json.JSONObject;
import org.json.JSONTokener;
import java.io.File;
import java.io.FileOutputStream;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import static org.junit.Assert.*;

public class WindowInsetsTest {
 @Rule public ActivityTestRule<MainActivity> rule=new ActivityTestRule<>(MainActivity.class);
 String js(String expression)throws Exception{
  final String[] result={null};CountDownLatch done=new CountDownLatch(1);
  InstrumentationRegistry.getInstrumentation().runOnMainSync(()->rule.getActivity().web.evaluateJavascript(expression,value->{result[0]=value;done.countDown();}));
  assertTrue("JavaScript callback timed out",done.await(10,TimeUnit.SECONDS));return result[0];
 }
 void waitForPage()throws Exception{
  long end=SystemClock.uptimeMillis()+20000;
  while(SystemClock.uptimeMillis()<end){if("true".equals(js("!!document.querySelector('#mobile-nav button')")))return;SystemClock.sleep(150);}
  fail("Bundled app did not render");
 }
 void checkSafeBounds(String name)throws Exception{
  waitForPage();SystemClock.sleep(600);
  InstrumentationRegistry.getInstrumentation().runOnMainSync(()->{
   MainActivity a=rule.getActivity();WindowInsetsCompat wi=ViewCompat.getRootWindowInsets(a.viewport);assertNotNull(wi);
   Insets safe=wi.getInsets(WindowInsetsCompat.Type.systemBars()|WindowInsetsCompat.Type.displayCutout()|WindowInsetsCompat.Type.ime());
   Rect content=new Rect();assertTrue(a.web.getGlobalVisibleRect(content));
   View decor=a.getWindow().getDecorView();int[] origin=new int[2];decor.getLocationOnScreen(origin);
   assertTrue("Header overlaps status bar: "+content+" top inset "+safe.top,content.top>=origin[1]+safe.top);
   assertTrue("Navigation overlaps system bar/keyboard: "+content,content.bottom<=origin[1]+decor.getHeight()-safe.bottom);
   assertTrue("Left cutout overlap",content.left>=origin[0]+safe.left);
   assertTrue("Right cutout overlap",content.right<=origin[0]+decor.getWidth()-safe.right);
   assertTrue("WebView must have useful height",content.height()>100);
  });
  JSONObject dom=new JSONObject((String)new JSONTokener(js("JSON.stringify({height:innerHeight,header:document.querySelector('body>header').getBoundingClientRect().top,nav:document.querySelector('#mobile-nav').getBoundingClientRect().bottom,navHeight:document.querySelector('#mobile-nav').getBoundingClientRect().height})")).nextValue());
  if(name.equals("portrait")||name.equals("landscape"))assertTrue("HTML header outside viewport",dom.getDouble("header")>=0);
  if(dom.getDouble("navHeight")>0)assertTrue("Fixed HTML navigation outside safe native viewport",dom.getDouble("nav")<=dom.getDouble("height")+1);
  Bitmap shot=InstrumentationRegistry.getInstrumentation().getUiAutomation().takeScreenshot();assertNotNull(shot);
  String mode=InstrumentationRegistry.getArguments().getString("navMode","unknown");
  File file=new File(rule.getActivity().getExternalFilesDir(null),mode+"-"+name+".png");
  try(FileOutputStream out=new FileOutputStream(file)){shot.compress(Bitmap.CompressFormat.PNG,100,out);}shot.recycle();
 }
 @Test public void portraitAndLandscapeStayInsideSystemBars()throws Exception{
  InstrumentationRegistry.getInstrumentation().runOnMainSync(()->rule.getActivity().setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT));
  checkSafeBounds("portrait");
  InstrumentationRegistry.getInstrumentation().runOnMainSync(()->rule.getActivity().setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE));
  SystemClock.sleep(1000);checkSafeBounds("landscape");
 }
 @Test public void keyboardHideRestoresSafeViewport()throws Exception{
  InstrumentationRegistry.getInstrumentation().runOnMainSync(()->rule.getActivity().setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT));waitForPage();
  js("document.querySelector('#search').scrollIntoView();document.querySelector('#search').focus();true");
  InstrumentationRegistry.getInstrumentation().runOnMainSync(()->{MainActivity a=rule.getActivity();a.web.requestFocus();((InputMethodManager)a.getSystemService(Context.INPUT_METHOD_SERVICE)).showSoftInput(a.web,InputMethodManager.SHOW_IMPLICIT);});
  long end=SystemClock.uptimeMillis()+8000;boolean shown=false;
  while(SystemClock.uptimeMillis()<end){final boolean[] visible={false};InstrumentationRegistry.getInstrumentation().runOnMainSync(()->visible[0]=ViewCompat.getRootWindowInsets(rule.getActivity().viewport).isVisible(WindowInsetsCompat.Type.ime()));if(visible[0]){shown=true;break;}SystemClock.sleep(150);}
  assertTrue("Keyboard must actually open for this check",shown);checkSafeBounds("keyboard");
  InstrumentationRegistry.getInstrumentation().runOnMainSync(()->{MainActivity a=rule.getActivity();((InputMethodManager)a.getSystemService(Context.INPUT_METHOD_SERVICE)).hideSoftInputFromWindow(a.web.getWindowToken(),0);});
  SystemClock.sleep(1000);checkSafeBounds("keyboard-hidden");
 }
}
