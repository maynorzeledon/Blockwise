package com.mayprep.blockwise;
import android.content.pm.ActivityInfo;
import android.graphics.Bitmap;
import android.graphics.Rect;
import android.os.SystemClock;
import android.view.View;
import android.view.MotionEvent;
import android.view.InputDevice;
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
  while(SystemClock.uptimeMillis()<end){if("true".equals(js("!!document.querySelector('#mobile-nav button')&&!window.BlockwiseIntroActive"))){
   final boolean[] focused={false};InstrumentationRegistry.getInstrumentation().runOnMainSync(()->focused[0]=rule.getActivity().hasWindowFocus());
   if(focused[0]){InstrumentationRegistry.getInstrumentation().waitForIdleSync();SystemClock.sleep(700);return;}
  }SystemClock.sleep(150);}
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
 @Test public void feedLoadsAndCategoryStripStaysPut()throws Exception{
  waitForPage();
  assertEquals("Hero should not hide the fact feed","false",js("!!document.querySelector('.hero')"));
  assertEquals("Initial feed batch","36",js("document.querySelectorAll('.feed-grid .card').length"));
  js("document.querySelector('#feed-end').scrollIntoView();true");
  long end=SystemClock.uptimeMillis()+8000;
  while(SystemClock.uptimeMillis()<end&&Integer.parseInt(js("document.querySelectorAll('.feed-grid .card').length"))<=36)SystemClock.sleep(100);
  assertTrue("Scrolling must automatically load more unique cards",Integer.parseInt(js("document.querySelectorAll('.feed-grid .card').length"))>36);
  assertEquals("No duplicate cards in this feed","true",js("(()=>{const a=[...document.querySelectorAll('.feed-grid .title-button')].map(b=>b.dataset.open);return new Set(a).size===a.length})()"));
  assertEquals("Category strip must retain its offset","true",js("(()=>{const strip=document.querySelector('.filterbar');strip.scrollLeft=220;const x=strip.scrollLeft;document.querySelector('[data-category=survival]').click();return Math.abs(document.querySelector('.filterbar').scrollLeft-x)<2})()"));
  js("document.querySelector('[data-category=all]').click();window.scrollTo(0,0);true");
 }
 @Test public void cardArtworkIsAboveBriefText()throws Exception{
  waitForPage();
  assertEquals("Artwork should sit above text at phone dimensions","true",js("(()=>{const c=document.querySelector('.feed-grid .card');return c.querySelector('.card-art').getBoundingClientRect().bottom<=c.querySelector('.cardbody').getBoundingClientRect().top+1})()"));
  assertEquals("Preview should be limited to three lines","3",js("Number(getComputedStyle(document.querySelector('.fact-preview')).webkitLineClamp)"));
  assertEquals("Sponge uses its actual block render","true",js("facts.find(f=>f.id==='sponge').image.src==='/reference-images/sponge.webp'"));
  assertEquals("Water fact uses its actual bucket item","true",js("facts.find(f=>f.id==='water').image.src==='/reference-images/water-bucket.webp'"));
 }
 @Test public void portraitAndLandscapeStayInsideSystemBars()throws Exception{
  InstrumentationRegistry.getInstrumentation().runOnMainSync(()->rule.getActivity().setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT));
  checkSafeBounds("portrait");
  InstrumentationRegistry.getInstrumentation().runOnMainSync(()->rule.getActivity().setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE));
  SystemClock.sleep(1000);checkSafeBounds("landscape");
 }
 @Test public void keyboardHideRestoresSafeViewport()throws Exception{
  InstrumentationRegistry.getInstrumentation().runOnMainSync(()->rule.getActivity().setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT));waitForPage();
  js("document.querySelector('#search').scrollIntoView({block:'center'});true");SystemClock.sleep(500);
  JSONObject field=new JSONObject((String)new JSONTokener(js("JSON.stringify((()=>{const r=document.querySelector('#search').getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2,width:innerWidth}})())")).nextValue());
  final int[] location=new int[2];final int[] width={0};
  InstrumentationRegistry.getInstrumentation().runOnMainSync(()->{rule.getActivity().web.getLocationOnScreen(location);width[0]=rule.getActivity().web.getWidth();});
  float scale=(float)(width[0]/field.getDouble("width"));float x=location[0]+(float)field.getDouble("x")*scale,y=location[1]+(float)field.getDouble("y")*scale;
  long now=SystemClock.uptimeMillis();MotionEvent down=MotionEvent.obtain(now,now,MotionEvent.ACTION_DOWN,x,y,0);down.setSource(InputDevice.SOURCE_TOUCHSCREEN);
  MotionEvent up=MotionEvent.obtain(now,now+100,MotionEvent.ACTION_UP,x,y,0);up.setSource(InputDevice.SOURCE_TOUCHSCREEN);
  assertTrue("Touch-down injection failed",InstrumentationRegistry.getInstrumentation().getUiAutomation().injectInputEvent(down,true));
  assertTrue("Touch-up injection failed",InstrumentationRegistry.getInstrumentation().getUiAutomation().injectInputEvent(up,true));down.recycle();up.recycle();
  long end=SystemClock.uptimeMillis()+8000;boolean shown=false;
  while(SystemClock.uptimeMillis()<end){final boolean[] visible={false};InstrumentationRegistry.getInstrumentation().runOnMainSync(()->visible[0]=ViewCompat.getRootWindowInsets(rule.getActivity().viewport).isVisible(WindowInsetsCompat.Type.ime()));if(visible[0]){shown=true;break;}SystemClock.sleep(150);}
  assertTrue("Keyboard must actually open for this check",shown);checkSafeBounds("keyboard");
  InstrumentationRegistry.getInstrumentation().runOnMainSync(()->{MainActivity a=rule.getActivity();((InputMethodManager)a.getSystemService(Context.INPUT_METHOD_SERVICE)).hideSoftInputFromWindow(a.web.getWindowToken(),0);});
  SystemClock.sleep(1000);checkSafeBounds("keyboard-hidden");
 }
 @Test public void arcadeHasCompletePoolsHiddenAnswersAndAlignedCrossword()throws Exception{
  waitForPage();
  assertEquals("Complete item registry","1506",js("ArcadeCatalog.items.length"));
  assertEquals("Complete block registry","1168",js("ArcadeCatalog.blocks.length"));
  js("page='games';arcadeStart('blocks',true);true");
  assertEquals("Answer artwork stays hidden","0",js("document.querySelectorAll('#main img').length"));
  js("arcadeStart('crossword',true);true");
  assertEquals("Crossword has real columns","true",js("(()=>{const rows=[...document.querySelectorAll('.arcade-cross-table tr')];const cells=rows[0].children;return rows.length>1&&cells.length>1&&cells[1].getBoundingClientRect().left>cells[0].getBoundingClientRect().left})()"));
  js("arcadeStart('memory',true);arcadeFlip(0);arcadeFlip(arcadeGame.cards.findIndex(id=>id!==arcadeGame.cards[0]));true");
  assertEquals("A pair is visible","2",js("arcadeGame.flips.length"));SystemClock.sleep(1400);
  assertEquals("Mismatch automatically turns back","0",js("arcadeGame.flips.length"));
 }

}
