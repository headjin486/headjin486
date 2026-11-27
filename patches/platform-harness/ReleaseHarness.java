package com.earthunlock.releaseharness;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Context;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import android.database.sqlite.SQLiteException;
import android.os.Bundle;
import java.lang.reflect.*;
import java.security.MessageDigest;
import java.nio.charset.StandardCharsets;
import java.util.*;

public final class ReleaseHarness extends Instrumentation {
    private Bundle args;
    private Context ctx;
    private Class<?> storeClass, pointClass;
    private Constructor<?> pointConstructor;
    private Method recordMethod;
    private SharedPreferences fixture;
    private static final double[][] POINTS = {
        {36.12,128.34,5,1700000000000L},
        {36.12009,128.34,5,1700000008000L},
        {36.12018,128.34008,5,1700000016000L},
        {36.12618,128.34008,6,1700000056000L},
        {36.12018,128.34008,5,1700000096000L},
        {0.001,179.9998,5,1700000400000L},
        {0.001,-179.9998,5,1700000410000L},
        {80.0000,10.0000,5,1700000700000L},
        {80.00005,10.0002,5,1700000710000L}
    };
    @Override public void onCreate(Bundle arguments) {
        super.onCreate(arguments); args = arguments; start();
    }
    @Override public void onStart() {
        Bundle result = new Bundle();
        try {
            ctx=getTargetContext();
            storeClass=type("TrackStore"); pointClass=type("TrackPoint");
            pointConstructor=pointClass.getDeclaredConstructor(double.class,double.class,float.class,long.class);
            pointConstructor.setAccessible(true);
            recordMethod=storeClass.getDeclaredMethod("recordAndReveal",pointClass,double.class);
            recordMethod.setAccessible(true);
            fixture=ctx.getSharedPreferences("platform_release_fixture",Context.MODE_PRIVATE);
            String mode=args.getString("mode");
            String version=ctx.getPackageManager().getPackageInfo(ctx.getPackageName(),0).versionName;
            if ("seed".equals(mode)) {
                require("0.10.50".equals(version),"seed version mismatch");
                seed();
                result.putString("stream","\nPASS: old app baseline seeded and golden records saved\n");
            } else if ("verify".equals(mode)) {
                require("0.10.51".equals(version),"update version mismatch");
                verifyUpgrade();
                verifyResources();
                verifyContours();
                result.putString("stream","\nPASS: existing GPS records, explored cells, area/distance, transaction rollback, OAuth resources and contour topology\n");
            } else throw new IllegalArgumentException("Unknown mode "+mode);
            finish(Activity.RESULT_OK,result);
        } catch (Throwable e) {
            result.putString("stream","\nFAIL: "+android.util.Log.getStackTraceString(e)+"\n");
            finish(Activity.RESULT_CANCELED,result);
        }
    }
    private Class<?> type(String name) throws Exception {
        return Class.forName("com.earthunlock.app."+name,true,ctx.getClassLoader());
    }
    private void require(boolean b,String msg) { if(!b) throw new AssertionError(msg); }
    private SQLiteOpenHelper open() throws Exception {
        Constructor<?> c=storeClass.getDeclaredConstructor(Context.class); c.setAccessible(true);
        return (SQLiteOpenHelper)c.newInstance(ctx);
    }
    private void record(SQLiteOpenHelper s,double[] p) throws Exception {
        recordMethod.invoke(s,pointConstructor.newInstance(p[0],p[1],(float)p[2],(long)p[3]),12.0);
    }
    private Number stat(SQLiteOpenHelper s,String method) throws Exception {
        Method m=storeClass.getDeclaredMethod(method);m.setAccessible(true);return (Number)m.invoke(s);
    }
    private String fingerprint(SQLiteOpenHelper s) throws Exception {
        MessageDigest md=MessageDigest.getInstance("SHA-256");
        SQLiteDatabase db=s.getReadableDatabase();
        try(Cursor c=db.rawQuery("SELECT cell_x,cell_y FROM explored_cells ORDER BY cell_x,cell_y",null)){
            while(c.moveToNext()) md.update((c.getLong(0)+":"+c.getLong(1)+"\n").getBytes(StandardCharsets.UTF_8));
        }
        try(Cursor c=db.rawQuery("SELECT lat,lon,accuracy,time FROM points ORDER BY time,_id",null)){
            while(c.moveToNext()) md.update((Double.doubleToLongBits(c.getDouble(0))+":"+Double.doubleToLongBits(c.getDouble(1))+":"+Float.floatToIntBits(c.getFloat(2))+":"+c.getLong(3)+"\n").getBytes(StandardCharsets.UTF_8));
        }
        StringBuilder b=new StringBuilder();for(byte v:md.digest()) b.append(String.format(Locale.US,"%02x",v&255));return b.toString();
    }
    private void save(SQLiteOpenHelper s,String prefix) throws Exception {
        long cells=stat(s,"exploredCellCount").longValue();require(cells>0,"No explored cells");
        require(fixture.edit().putInt(prefix+"points",stat(s,"count").intValue())
            .putLong(prefix+"cells",cells).putString(prefix+"hash",fingerprint(s))
            .putLong(prefix+"area",Double.doubleToLongBits(stat(s,"exploredAreaSquareMeters").doubleValue()))
            .putLong(prefix+"distance",Double.doubleToLongBits(stat(s,"distanceMeters").doubleValue())).commit(),"Fixture commit failed");
    }
    private void check(SQLiteOpenHelper s,String prefix) throws Exception {
        require(stat(s,"count").intValue()==fixture.getInt(prefix+"points",-1),"point count changed");
        require(stat(s,"exploredCellCount").longValue()==fixture.getLong(prefix+"cells",-1),"cell count changed");
        require(fingerprint(s).equals(fixture.getString(prefix+"hash","")),"record or cell coordinate fingerprint changed");
        require(Math.abs(stat(s,"exploredAreaSquareMeters").doubleValue()-Double.longBitsToDouble(fixture.getLong(prefix+"area",0)))<0.00001,"area changed");
        require(Math.abs(stat(s,"distanceMeters").doubleValue()-Double.longBitsToDouble(fixture.getLong(prefix+"distance",0)))<0.000001,"distance changed");
    }
    private void seed() throws Exception {
        try(SQLiteOpenHelper s=open()){
            require(stat(s,"count").intValue()==0,"seed requires isolated empty history");
            for(double[] p:POINTS) record(s,p);save(s,"full");
        }
        require(ctx.deleteDatabase("earth_explorer.db"),"failed to reset synthetic database");
        try(SQLiteOpenHelper s=open()){
            for(int i=0;i<3;i++) record(s,POINTS[i]);save(s,"initial");
        }
    }
    private void verifyUpgrade() throws Exception {
        try(SQLiteOpenHelper s=open()){
            check(s,"initial");
            for(int i=3;i<POINTS.length;i++)record(s,POINTS[i]);
            check(s,"full");
            SQLiteDatabase db=s.getWritableDatabase();
            db.execSQL("UPDATE app_stats SET distance_meters=NULL,last_lat=NULL,last_lon=NULL,last_accuracy=NULL,last_time=NULL,explored_area_m2=NULL WHERE _id=1");
            check(s,"full");
            db.execSQL("CREATE TRIGGER platform_abort BEFORE INSERT ON explored_cells BEGIN SELECT RAISE(ABORT,'regression test'); END");
            boolean failed=false;
            try {record(s,new double[]{80.00010,10.00040,5,1700000720000L});}
            catch(InvocationTargetException e) {if(e.getCause() instanceof SQLiteException) failed=true;else throw e;}
            finally {db.execSQL("DROP TRIGGER platform_abort");}
            require(failed,"Injected SQLite failure not triggered");check(s,"full");
        }
        try(SQLiteOpenHelper s=open()){check(s,"full");}
    }
    private void verifyResources() {
        int id=ctx.getResources().getIdentifier("default_web_client_id","string",ctx.getPackageName());
        require(id!=0 && ctx.getString(id).endsWith(".apps.googleusercontent.com"),"OAuth resource removed");
        id=ctx.getResources().getIdentifier("project_id","string",ctx.getPackageName());
        require(id!=0 && "my-earth-a73cb".equals(ctx.getString(id)),"Firebase project resource changed");
    }
    private void verifyContours() throws Exception {
        Class<?> cell=type("ExploredCell"), contours=type("FogContours"),shapeClass=type("FogContours$Shape");
        Constructor<?> c=cell.getDeclaredConstructor(double.class,double.class,int.class);c.setAccessible(true);
        List<Object> cells=new ArrayList<>();
        long gx=Math.round(6371000.0*Math.toRadians(128.34)/5),gy=Math.round(6371000.0*Math.toRadians(36.12)/5);
        for(int dx=-5;dx<=5;dx++)for(int dy=-5;dy<=5;dy++)if(Math.abs(dx)>1||Math.abs(dy)>1) cells.add(c.newInstance((double)(gx+dx),(double)(gy+dy),1));
        cells.add(c.newInstance((double)(gx+9),(double)gy,1));
        Method build=null;for(Method m:contours.getDeclaredMethods())if(m.getName().startsWith("build")&&m.getParameterCount()==1&&m.getReturnType()==shapeClass){build=m;break;}
        require(build!=null,"Contour build method absent");build.setAccessible(true);
        Object instance=null;if(!Modifier.isStatic(build.getModifiers())){Field field=contours.getDeclaredField("INSTANCE");field.setAccessible(true);instance=field.get(null);}
        Object shape=build.invoke(instance,cells);Method getRings=shapeClass.getDeclaredMethod("getRings");getRings.setAccessible(true);
        List<?> rings=(List<?>)getRings.invoke(shape);
        require(rings!=null&&rings.size()==3,"Expected exterior, hole and standalone cell, got "+(rings==null?"null":rings.size()));
    }
}
