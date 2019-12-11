#bt2390_ictcp
#reinhard_xyy
#reinhard_yuv
#reinhard_rgby
#bt2390_new
#reinhard_new


import vapoursynth as vs


def bt2390_ictcp(clip="",source_peak=None,target_nits="" ) :
    core = vs.get_core()
    c=clip
    
    if source_peak is None:
       source_peak=c.get_frame(0).props.MasteringDisplayMaxLuminance

       
    primaries = "2020"    
    source_peak=source_peak
    matrix_in_s="2020ncl"
    transfer_in_s="st2084"    
    exposure_bias1=source_peak/target_nits
    source_peak=source_peak 
    width=c.width
    height=c.height    
    width_n=1920
    height_n=(height*width_n)/width


    c=core.resize.Bicubic(clip=c, format=vs.YUV444PS, filter_param_a=0,width=width_n,height=height_n, filter_param_b=0.75,chromaloc_in_s="center",chromaloc_s="center", range_in_s="limited", range_s="full",dither_type="none")
    

    lw = source_peak/10000   
    #eotf^-1  y=((x^0.1593017578125) * 18.8515625 + 0.8359375  /   (x^0.1593017578125) * 18.6875 + 1)^78.84375
    lw = ((((lw ** 0.1593017578125) * 18.8515625) + 0.8359375)  /   (((lw ** 0.1593017578125) * 18.6875) + 1))**78.84375

    
    lmax=target_nits/10000
    #eotf^-1  y=((x^0.1593017578125) * 18.8515625 + 0.8359375  /   (x^0.1593017578125) * 18.6875 + 1)^78.84375
    lmax = ((((lmax ** 0.1593017578125) * 18.8515625) + 0.8359375)  /   (((lmax ** 0.1593017578125) * 18.6875) + 1))**78.84375    
   
    #maxlum=(lmax-0)/(lw-0) ==> maxlum=lmax/lw
    maxlum=lmax/lw  
    
    #ks1=(1.5*lmax)- 0.5      
    ks1=(1.5*lmax)- 0.5
    
    #ks2=(1.5*maxlum)- 0.5
    ks2=(1.5*maxlum)- 0.5 
    
    #ks=(ks1+ks2)/2    
    ks=(ks1+ks2)/2

     
    
    c_ictcp=core.resize.Bicubic(clip=c, format=vs.YUV444PS, filter_param_a=0, filter_param_b=0.75,chromaloc_in_s="center", transfer_in_s=transfer_in_s,chromaloc_s="center", range_in_s="full", range_s="full",dither_type="none", nominal_luminance=source_peak, matrix_in_s=matrix_in_s, matrix_s="ictcp")

 
    I=core.std.ShufflePlanes(c_ictcp, planes=[0], colorfamily=vs.GRAY)
    ct=core.std.ShufflePlanes(c_ictcp, planes=[1], colorfamily=vs.GRAY)
    cp=core.std.ShufflePlanes(c_ictcp, planes=[2], colorfamily=vs.GRAY)
   
    lum_notclipped=I
   
    I=core.std.Limiter(I, 0,lw,planes=[0])      
    
    lum=I
    saturation_mult=core.std.Expr(clips=[lum,lum_notclipped], expr=" x   y / y x / min ")
    saturation_mult=core.std.Limiter(saturation_mult, 0,1)
   

    ct=core.std.Expr(clips=[ct,saturation_mult], expr=" x y * ")
    cp=core.std.Expr(clips=[cp,saturation_mult], expr=" x y * ")

    
    saturation_mult1=core.std.Expr(clips=[lum], expr=" x {lmax} -     {lw} {lmax} -  / ".format(lw=lw,lmax=lmax))
    saturation_mult1=core.std.Limiter(saturation_mult1, 0,1)    
    saturation_mult1=core.std.Expr(clips=[saturation_mult1], expr=" 1 x 0.5 * - ")

    ct=core.std.Expr(clips=[ct,saturation_mult1], expr=" x y *  ")
    cp=core.std.Expr(clips=[cp,saturation_mult1], expr=" x y *  ")
       
    

    #e1=(x-0)/(lw-0) ==> e1= x / lw
    e1=core.std.Expr(clips=[I], expr="x  {lw} /".format(lw=lw))
    t = core.std.Expr(clips=[e1], expr="x {ks} - 1 {ks} - / ".format(ks=ks))    
    #p=(2t^3 - 3t^2 +1)*ks +( t^3-2t^2+t)*(1-ks)+(-2t^3+3t^2)* maxlum     
    p = core.std.Expr(clips=[t], expr="  2 x 3 pow *  3 x 2 pow   * - 1 + {ks} * 1 {ks} - x 3 pow  2 x 2 pow *    -   x  + * + -2 x 3 pow  *  3 x 2 pow  *  + {maxlum} * +".format(ks=ks,maxlum=maxlum))    
    e2=core.std.Expr(clips=[e1,p], expr="x {ks} < x y ? ".format(ks=ks))
    #e3=e2+0*(1-e2)^4 ==> e3=e2
  
     
    #invert the normalization of the PQ values
    #e4=[e3*(lw-0)]+0  ==> e4=e3*lw
    I=core.std.Expr(clips=[e2], expr="x  {lw} * ".format(lw=lw))
   

    I=core.std.Limiter(I, 0,1,planes=[0]) 
    lumtm=I
    
    
    saturation_mult2=core.std.Expr(clips=[lum,lumtm], expr=" x   y / y x / min ")
    saturation_mult2=core.std.Limiter(saturation_mult2, 0,1)
   

    ct=core.std.Expr(clips=[ct,saturation_mult2], expr=" x y * ")
    cp=core.std.Expr(clips=[cp,saturation_mult2], expr=" x y * ")

    c_ictcp=core.std.ShufflePlanes(clips=[I,ct,cp], planes=[0,0,0], colorfamily=vs.YUV)

    c_ictcp=core.resize.Bicubic(clip=c_ictcp, format=vs.RGBS, filter_param_a=0, filter_param_b=0.75,chromaloc_in_s="center", transfer_in_s=transfer_in_s,transfer_s=transfer_in_s,chromaloc_s="center", range_in_s="full", range_s="full",dither_type="none", nominal_luminance=target_nits, matrix_in_s="ictcp")

    c=core.resize.Bicubic(clip=c, format=vs.RGBS, filter_param_a=0, filter_param_b=0.75,chromaloc_in_s="center", chromaloc_s="center", range_in_s="full", range_s="full",dither_type="none", matrix_in_s="2020ncl")
    c=core.std.Limiter(c, 0,lw)    
   
    e1=core.std.Expr(clips=[c], expr="x  {lw} /".format(lw=lw))
    t = core.std.Expr(clips=[e1], expr="x {ks} - 1 {ks} - / ".format(ks=ks))    
    p = core.std.Expr(clips=[t], expr="  2 x 3 pow *  3 x 2 pow   * - 1 + {ks} * 1 {ks} - x 3 pow  2 x 2 pow *    -   x  + * + -2 x 3 pow  *  3 x 2 pow  *  + {maxlum} * +".format(ks=ks,maxlum=maxlum))    
    e2=core.std.Expr(clips=[e1,p], expr="x {ks} < x y ? ".format(ks=ks))
    c=core.std.Expr(clips=[e2], expr="x  {lw} * ".format(lw=lw))   

    c=core.std.Limiter(c, 0,1)
    c=core.std.Merge(c_ictcp, c, 0.5)    
      
   
    c=core.resize.Bicubic(clip=c, format=vs.RGBS, transfer_in_s=transfer_in_s, transfer_s="linear",dither_type="none", nominal_luminance=target_nits)
    c=core.resize.Bicubic(clip=c, format=vs.RGBS, primaries_in_s=primaries, primaries_s="709",dither_type="none")
    c=core.resize.Bicubic(clip=c, format=vs.RGBS, transfer_in_s="linear", transfer_s="709",dither_type="none")
    c=core.std.Limiter(c, 0,1)


    c=core.resize.Bicubic(clip=c, format=vs.YUV422P16,matrix_s="709", filter_param_a=0, filter_param_b=0.75, range_in_s="full",range_s="limited", chromaloc_in_s="center", chromaloc_s="center",dither_type="none")  
      
    return c


def reinhard_xyy(clip="",source_peak=None,target_nits="" ) :
    core = vs.get_core()
    c=clip
    
    if source_peak is None:
       source_peak=c.get_frame(0).props.MasteringDisplayMaxLuminance

       
    primaries = "2020"    
    source_peak=source_peak
    matrix_in_s="2020ncl"
    transfer_in_s="st2084"    
    exposure_bias1=source_peak/target_nits
    source_peak=source_peak 
    width=c.width
    height=c.height    
    width_n=1920
    height_n=(height*width_n)/width


    c=core.resize.Bicubic(clip=c, format=vs.YUV444PS, filter_param_a=0,width=width_n,height=height_n, filter_param_b=0.75,chromaloc_in_s="center",chromaloc_s="center", range_in_s="limited", range_s="full",dither_type="none")

    c=core.resize.Bicubic(clip=c, format=vs.RGBS, filter_param_a=0, filter_param_b=0.75,chromaloc_in_s="center", transfer_in_s=transfer_in_s,transfer_s="linear",chromaloc_s="center", range_in_s="full", range_s="full",dither_type="none", nominal_luminance=source_peak, matrix_in_s=matrix_in_s)
    
    c = core.std.Expr(clips=[c], expr=" x {exposure_bias1} * ".format(exposure_bias1=exposure_bias1))
    
    tm_rgb = core.std.Expr(clips=[c], expr="  x {exposure_bias1} {exposure_bias1} * / 1 + x *  x 1 + /".format(exposure_bias1=exposure_bias1))
    
    c=core.resize.Bicubic(clip=c, format=vs.RGBS, primaries_in_s=primaries, primaries_s="st428" ,dither_type="none")
    X=core.std.ShufflePlanes(c, planes=[0], colorfamily=vs.GRAY)
    Y=core.std.ShufflePlanes(c, planes=[1], colorfamily=vs.GRAY)
    Z=core.std.ShufflePlanes(c, planes=[2], colorfamily=vs.GRAY)
    
    x=core.std.Expr(clips=[X,Y,Z], expr=" x x y + z + /    ")
    y=core.std.Expr(clips=[X,Y,Z], expr=" y x y + z + /    ")
    Y=Y
    
    
    y1=Y
    Y = core.std.Expr(clips=[Y], expr="  x {exposure_bias1} {exposure_bias1} * / 1 + x *  x 1 + /".format(exposure_bias1=exposure_bias1))

   
    y2=Y
    y2=core.std.Limiter(y2,0,1)
    saturation_mult=core.std.Expr(clips=[y1], expr=" x 1 -     {exposure_bias1} 1 -  / ".format(exposure_bias1=exposure_bias1,target_nits=target_nits))
    saturation_mult=core.std.Limiter(saturation_mult, 0,1) 
    saturation_mult=core.std.Expr(clips=[saturation_mult], expr="1  x 0.5 * - ")
       
  

    
    x=  core.std.Expr(clips=[x,saturation_mult], expr=" x 1 3 /  - y * 1 3 / +  ")
    y=  core.std.Expr(clips=[y,saturation_mult], expr=" x 1 3 /  - y * 1 3 / +   ")    
        




    X= core.std.Expr(clips=[x,y,Y], expr=" x z * y /   ")
    Y=Y
    Z=core.std.Expr(clips=[x,y,Y], expr=" 1 x - y - z * y /   ")
    tm_xyy=  core.std.ShufflePlanes(clips=[X,Y,Z], planes=[0,0,0], colorfamily=vs.RGB)    
    
    tm_xyy=core.resize.Bicubic(clip=tm_xyy, format=vs.RGBS, primaries_in_s="st428" , primaries_s="2020",dither_type="none")
    c=  core.std.Merge(tm_xyy, tm_rgb, 0.5)
    c=core.resize.Bicubic(clip=c, format=vs.RGBS, primaries_in_s="2020" , primaries_s="709",dither_type="none")
    
    
    c=core.resize.Bicubic(clip=c, format=vs.RGBS, transfer_in_s="linear", transfer_s="709",dither_type="none")
    c=core.std.Limiter(c, 0,1)

    c=core.resize.Bicubic(clip=c, format=vs.YUV422P16,matrix_s="709", filter_param_a=0, filter_param_b=0.75, range_in_s="full",range_s="limited", chromaloc_in_s="center", chromaloc_s="center",dither_type="none")  
      
    return c





def reinhard_yuv(clip="",source_peak=None,target_nits="" ) :
    core = vs.get_core()
    c=clip
    
    if source_peak is None:
       source_peak=c.get_frame(0).props.MasteringDisplayMaxLuminance

       
    primaries = "2020"    
    source_peak=source_peak
    matrix_in_s="2020ncl"
    transfer_in_s="st2084"    
    exposure_bias1=source_peak/target_nits
    source_peak=source_peak 
    width=c.width
    height=c.height    
    width_n=1920
    height_n=(height*width_n)/width


    c=core.resize.Bicubic(clip=c, format=vs.YUV444PS, filter_param_a=0,width=width_n,height=height_n, filter_param_b=0.75,chromaloc_in_s="center",chromaloc_s="center", range_in_s="limited", range_s="full",dither_type="none")

    c=core.resize.Bicubic(clip=c, format=vs.RGBS, filter_param_a=0, filter_param_b=0.75,chromaloc_in_s="center", transfer_in_s=transfer_in_s,transfer_s="linear",chromaloc_s="center", range_in_s="full", range_s="full",dither_type="none", nominal_luminance=source_peak, matrix_in_s=matrix_in_s)
    
    
    c = core.std.Expr(clips=[c], expr=" x {exposure_bias1} * ".format(exposure_bias1=exposure_bias1))
    crgb = core.std.Expr(clips=[c], expr="  x {exposure_bias1} {exposure_bias1} * / 1 + x *  x 1 + /".format(exposure_bias1=exposure_bias1))
 
    c=core.resize.Bicubic(clip=c, format=vs.YUV444PS, filter_param_a=0, filter_param_b=0.75,chromaloc_in_s="center",matrix_s=matrix_in_s,chromaloc_s="center", range_in_s="full", range_s="full",dither_type="none")
 

    


    y1=core.std.ShufflePlanes(c, planes=[0], colorfamily=vs.GRAY)   
    y1=core.std.ShufflePlanes(y1, planes=[0,0,0], colorfamily=vs.YUV)     
    
    saturation_mult1=core.std.Expr(clips=[y1], expr=" x 1  -     {exposure_bias1} 1 -  / ".format(exposure_bias1=exposure_bias1,target_nits=target_nits))
    saturation_mult1=core.std.Limiter(saturation_mult1, 0,1)
    saturation_mult1=core.std.Expr(clips=[saturation_mult1], expr=" 1 x 0.5 * - ".format(exposure_bias1=exposure_bias1))
        
    saturation_mult1=core.std.ShufflePlanes(saturation_mult1, planes=[0,0,0], colorfamily=vs.YUV)
    c = core.std.Expr(clips=[c,saturation_mult1], expr=["  x "," x y *  "," x y *  "])
    
    
      
    
    c = core.std.Expr(clips=[c], expr=["  x {exposure_bias1} {exposure_bias1} * / 1 + x *  x 1 + /".format(exposure_bias1=exposure_bias1),"",""])

    y2=core.std.ShufflePlanes(c, planes=[0], colorfamily=vs.GRAY)
    y2_notclipped=y2
    y2=core.std.Limiter(y2,0,1)
    y2_notclipped=core.std.ShufflePlanes(y2_notclipped, planes=[0,0,0], colorfamily=vs.YUV)
    
    y2=core.std.ShufflePlanes(y2, planes=[0,0,0], colorfamily=vs.YUV)

    saturation_mult2=core.std.Expr(clips=[y2_notclipped,y2], expr=" x   y / y x / min ")
    saturation_mult2=core.std.Limiter(saturation_mult2, 0,1) 
    saturation_mult2=core.std.ShufflePlanes(saturation_mult2, planes=[0,0,0], colorfamily=vs.YUV)

    c=core.std.Expr(clips=[c,saturation_mult2], expr=[" x "," x y * "," x y * "]) 
    c=core.std.Limiter(c, 0,1,planes=0) 
      
    saturation_mult3=core.std.Expr(clips=[y1,y2], expr=" x   y / y x / min ")
    saturation_mult3=core.std.Limiter(saturation_mult3, 0,1) 
    saturation_mult3=core.std.ShufflePlanes(saturation_mult3, planes=[0,0,0], colorfamily=vs.YUV)

    c=core.std.Expr(clips=[c,saturation_mult3], expr=[" x "," x y * "," x y * "])
    

      
    c=core.resize.Bicubic(clip=c, format=vs.RGBS, filter_param_a=0, filter_param_b=0.75,chromaloc_in_s="center",chromaloc_s="center", range_in_s="full", range_s="full",dither_type="none", nominal_luminance=source_peak, matrix_in_s=matrix_in_s)
    
    c=core.std.Merge(c, crgb, 0.5) 
     


    
    c=core.resize.Bicubic(clip=c, format=vs.RGBS, primaries_in_s="2020" , primaries_s="709",dither_type="none")
    
    c=core.resize.Bicubic(clip=c, format=vs.RGBS, transfer_in_s="linear", transfer_s="709",dither_type="none")
    c=core.std.Limiter(c, 0,1)

    c=core.resize.Bicubic(clip=c, format=vs.YUV422P16,matrix_s="709", filter_param_a=0, filter_param_b=0.75, range_in_s="full",range_s="limited", chromaloc_in_s="center", chromaloc_s="center",dither_type="none")  
      
    return c





def reinhard_rgby(clip="",source_peak=None,target_nits="" ) :
    core = vs.get_core()
    c=clip
    
    if source_peak is None:
       source_peak=c.get_frame(0).props.MasteringDisplayMaxLuminance

       
    primaries = "2020"    
    source_peak=source_peak
    matrix_in_s="2020ncl"
    transfer_in_s="st2084"    
    exposure_bias1=source_peak/target_nits
    source_peak=source_peak 
    width=c.width
    height=c.height    
    width_n=1920
    height_n=(height*width_n)/width
    
    
    
    c=core.resize.Bicubic(clip=c, format=vs.YUV444PS, filter_param_a=0,width=width_n,height=height_n, filter_param_b=0.75,chromaloc_in_s="center",chromaloc_s="center", range_in_s="limited", range_s="full",dither_type="none")

    c=core.resize.Bicubic(clip=c, format=vs.RGBS, filter_param_a=0, filter_param_b=0.75,chromaloc_in_s="center", transfer_in_s=transfer_in_s,transfer_s="linear",chromaloc_s="center", range_in_s="full", range_s="full",dither_type="none", nominal_luminance=source_peak, matrix_in_s=matrix_in_s)
    
    
    c = core.std.Expr(clips=[c], expr=" x {exposure_bias1} * ".format(exposure_bias1=exposure_bias1))
    o=c
    r=core.std.ShufflePlanes(c, planes=[0], colorfamily=vs.GRAY)
    g=core.std.ShufflePlanes(c, planes=[1], colorfamily=vs.GRAY)
    b=core.std.ShufflePlanes(c, planes=[2], colorfamily=vs.GRAY) 
    
    y1 = core.std.Expr(clips=[r,g,b], expr=" 0.2627 x * 0.6780 y * + 0.0593 z * + ")#hardcoded for bt.2020
    y1=core.std.ShufflePlanes(y1, planes=[0], colorfamily=vs.RGB)
    c = core.std.Expr(clips=[c], expr="  x {exposure_bias1} {exposure_bias1} * / 1 + x *  x 1 + /".format(exposure_bias1=exposure_bias1))
    crgb=c    
    r2=core.std.ShufflePlanes(c, planes=[0], colorfamily=vs.GRAY)
    g2=core.std.ShufflePlanes(c, planes=[1], colorfamily=vs.GRAY)
    b2=core.std.ShufflePlanes(c, planes=[2], colorfamily=vs.GRAY)     
    y2 = core.std.Expr(clips=[r2,g2,b2], expr=" 0.2627 x * 0.6780 y * + 0.0593 z * + ")#hardcoded for bt.2020
    y2=core.std.ShufflePlanes(y2, planes=[0], colorfamily=vs.RGB)
    y2=core.std.Limiter(y2,0,1)


    



    saturation_mult=core.std.Expr(clips=[y1], expr=" x 1 -     {exposure_bias1} 1 -  / ".format(exposure_bias1=exposure_bias1,target_nits=target_nits))
    saturation_mult=core.std.Limiter(saturation_mult, 0,1)
    saturation_mult=core.std.Expr(clips=[saturation_mult], expr=" 1 x 0.5 * - ".format(exposure_bias1=exposure_bias1))
        



    c = core.std.Expr(clips=[o,y1,saturation_mult,y2,crgb], expr="y  z   x y - * +   y / a * 0.5 * b 0.5 * +".format(exposure_bias1=exposure_bias1))


    c=core.resize.Bicubic(clip=c, format=vs.RGBS, primaries_in_s="2020" , primaries_s="709",dither_type="none")
    
    c=core.resize.Bicubic(clip=c, format=vs.RGBS, transfer_in_s="linear", transfer_s="709",dither_type="none")
    c=core.std.Limiter(c, 0,1)

    c=core.resize.Bicubic(clip=c, format=vs.YUV422P16,matrix_s="709", filter_param_a=0, filter_param_b=0.75, range_in_s="full",range_s="limited", chromaloc_in_s="center", chromaloc_s="center",dither_type="none")  
      
    return c


def bt2390_new(clip="",source_peak=None,target_nits="",transfer=None,matrix=None,primaries=None ) :
    core = vs.get_core()
    c=clip
    if source_peak is None:
       source_peak=c.get_frame(0).props.MasteringDisplayMaxLuminance    

    if transfer is None:  
       transfer=c.get_frame(0).props._Transfer
    if matrix is None:    
       matrix=c.get_frame(0).props._Matrix
    if transfer == 16 :
       transfer = "st2084"
    if transfer == 18 :   
       transfer = "std-b67"
    if matrix == 9 :
       matrix = "2020ncl"   
    if primaries is None:  
       primaries=c.get_frame(0).props._Primaries
    if primaries == 9 :
       primaries = "2020"
    if primaries == 1 :
       primaries = "709" 
       
       
 
    source_peak=source_peak
    matrix_in_s=matrix
    transfer_in_s=transfer
    


    source_peak=source_peak 

    width=c.width
    height=c.height    
    width_n=1920
    height_n=(height*width_n)/width
    
    
    
    c=core.resize.Bicubic(clip=c, format=vs.RGBS, filter_param_a=0, filter_param_b=0.75, matrix_in_s=matrix_in_s,chromaloc_in_s="center",chromaloc_s="center", range_in_s="limited", range_s="full",dither_type="none")
    cy=c
    r=core.std.ShufflePlanes(c, planes=[0], colorfamily=vs.GRAY)
    g=core.std.ShufflePlanes(c, planes=[1], colorfamily=vs.GRAY)
    b=core.std.ShufflePlanes(c, planes=[2], colorfamily=vs.GRAY)
    max = core.std.Expr(clips=[r,g,b], expr="   x y max z max  ")
    
    y = core.std.Expr(clips=[r,g,b], expr=" 0.2627 x * 0.6780 y * + 0.0593 z * + ")
    satrgb1= core.std.Expr(clips=[y,max], expr="   x  y + 2 /  ")
    lw = source_peak/10000   
    lw = ((((lw ** 0.1593017578125) * 18.8515625) + 0.8359375)  /   (((lw ** 0.1593017578125) * 18.6875) + 1))**78.84375

    
    lmax=target_nits/10000
    lmax = ((((lmax ** 0.1593017578125) * 18.8515625) + 0.8359375)  /   (((lmax ** 0.1593017578125) * 18.6875) + 1))**78.84375    


    e1=core.std.Expr(clips=[c], expr="x  {lw} /".format(lw=lw))
    e1=core.std.Limiter(e1, 0,1)      
    e1y=core.std.Expr(clips=[satrgb1], expr="x  {lw} /".format(lw=lw))
    e1y=core.std.Limiter(e1y, 0,1)      
 
        
    maxlum=lmax/lw  
    
    ks1=(1.5*lmax)- 0.5
    
    ks2=(1.5*maxlum)- 0.5 
    
    ks=(ks1+ks2)/2
    
    t = core.std.Expr(clips=[e1], expr="x {ks} - 1 {ks} - / ".format(ks=ks))
    ty = core.std.Expr(clips=[e1y], expr="x {ks} - 1 {ks} - / ".format(ks=ks))
    
    p = core.std.Expr(clips=[t], expr="  2 x 3 pow *  3 x 2 pow   * - 1 + {ks} * 1 {ks} - x 3 pow  2 x 2 pow *    -   x  + * + -2 x 3 pow  *  3 x 2 pow  *  + {maxlum} * +".format(ks=ks,maxlum=maxlum))
    py = core.std.Expr(clips=[ty], expr="  2 x 3 pow *  3 x 2 pow   * - 1 + {ks} * 1 {ks} - x 3 pow  2 x 2 pow *    -   x  + * + -2 x 3 pow  *  3 x 2 pow  *  + {maxlum} * +".format(ks=ks,maxlum=maxlum))
    
    e2=core.std.Expr(clips=[e1,p], expr="x {ks} < x y ? ".format(ks=ks))
    e2y=core.std.Expr(clips=[e1y,py], expr="x {ks} < x y ? ".format(ks=ks))

 
     

    crgb=core.std.Expr(clips=[e2], expr="x  {lw} * ".format(lw=lw))
    satrgb2=core.std.Expr(clips=[e2y], expr="x  {lw} * ".format(lw=lw))
    

    satrgb1=core.std.ShufflePlanes(satrgb1, planes=[0], colorfamily=vs.RGB)
    
    satrgb2=core.std.ShufflePlanes(satrgb2, planes=[0], colorfamily=vs.RGB) 
    satrgbmult= core.std.Expr(clips=[satrgb1,satrgb2], expr="  y x /"   )    
    satrgbmult=core.std.ShufflePlanes(satrgbmult, planes=[0,0,0], colorfamily=vs.YUV)  
    satrgbmult=core.std.Limiter(satrgbmult, 0,1)     
    
    crgb=core.std.Limiter(crgb, 0,1)
    
    cy=core.resize.Bicubic(clip=cy, format=vs.YUV444PS, filter_param_a=0, filter_param_b=0.75,chromaloc_in_s="center",matrix_s=matrix_in_s,chromaloc_s="center", range_in_s="full", range_s="full",dither_type="none")
 
    crgb=core.resize.Bicubic(clip=crgb, format=vs.YUV444PS, filter_param_a=0, filter_param_b=0.75,chromaloc_in_s="center",matrix_s=matrix_in_s,chromaloc_s="center", range_in_s="full", range_s="full",dither_type="none") 
    


    y=core.std.ShufflePlanes(cy, planes=[0], colorfamily=vs.GRAY)

    e1y=core.std.Expr(clips=[y], expr="x  {lw} /".format(lw=lw))
    e1y=core.std.Limiter(e1y, 0,1)      
 
        

    ty = core.std.Expr(clips=[e1y], expr="x {ks} - 1 {ks} - / ".format(ks=ks))
    
    py = core.std.Expr(clips=[ty], expr="  2 x 3 pow *  3 x 2 pow   * - 1 + {ks} * 1 {ks} - x 3 pow  2 x 2 pow *    -   x  + * + -2 x 3 pow  *  3 x 2 pow  *  + {maxlum} * +".format(ks=ks,maxlum=maxlum))
    
    e2y=core.std.Expr(clips=[e1y,py], expr="x {ks} < x y ? ".format(ks=ks))

     
     
    e4y=core.std.Expr(clips=[e2y], expr="x  {lw} * ".format(lw=lw))
    cy = core.std.ShufflePlanes(clips=[e4y,cy,cy], planes=[0,1,2], colorfamily=vs.YUV)
    
       
    
    c=core.std.Expr(clips=[cy,satrgbmult], expr=[" x "," x y * "," x y * "])     


    c=core.std.Merge(c, crgb, 0.75)    
    
    
    
    
       
    c=core.resize.Bicubic(clip=c, format=vs.RGBS, transfer_in_s=transfer_in_s, transfer_s="linear",dither_type="none", nominal_luminance=target_nits)


   
    c=core.resize.Bicubic(clip=c, format=vs.RGBS, primaries_in_s=primaries, primaries_s="709",dither_type="none")
    c=core.std.Limiter(c, 0,1)
    
    c=core.std.Expr(clips=[c], expr="  x 1 2.2 / pow ")
    c=core.std.Limiter(c, 0,1)
    c=core.resize.Bicubic(clip=c, format=vs.RGB48, filter_param_a=0, filter_param_b=0.5, width=width_n,height=height_n,chromaloc_in_s="center",chromaloc_s="center",dither_type="none")
   
    c=core.resize.Bicubic(clip=c, format=vs.YUV422P16,matrix_s="709", filter_param_a=0, filter_param_b=0.75, range_in_s="full",range_s="limited", chromaloc_in_s="center", chromaloc_s="center",dither_type="none")  
      
    return c


def reinhard_new(clip="",source_peak=None,target_nits="" ) :
    core = vs.get_core()
    c=clip
    
    if source_peak is None:
       source_peak=c.get_frame(0).props.MasteringDisplayMaxLuminance

       
    primaries = "2020"    
    source_peak=source_peak
    matrix_in_s="2020ncl"
    transfer_in_s="st2084"    
    exposure_bias1=source_peak/target_nits
    source_peak=source_peak 
    width=c.width
    height=c.height    
    width_n=1920
    height_n=(height*width_n)/width


    c=core.resize.Bicubic(clip=c, format=vs.YUV444PS, filter_param_a=0,width=width_n,height=height_n, filter_param_b=0.5,chromaloc_in_s="center", resample_filter_uv="bicubic", filter_param_a_uv=0, filter_param_b_uv=0.5,chromaloc_s="center", range_in_s="limited", range_s="full",dither_type="none")

    c=core.resize.Bicubic(clip=c, format=vs.RGBS, filter_param_a=0, filter_param_b=0.75,chromaloc_in_s="center", transfer_in_s=transfer_in_s,transfer_s="linear",chromaloc_s="center", range_in_s="full", range_s="full",dither_type="none", nominal_luminance=source_peak, matrix_in_s=matrix_in_s)
    
    
    c = core.std.Expr(clips=[c], expr=" x {exposure_bias1} * ".format(exposure_bias1=exposure_bias1))
    r=core.std.ShufflePlanes(c, planes=[0], colorfamily=vs.GRAY)
    g=core.std.ShufflePlanes(c, planes=[1], colorfamily=vs.GRAY)
    b=core.std.ShufflePlanes(c, planes=[2], colorfamily=vs.GRAY) 
    max = core.std.Expr(clips=[r,g,b], expr="   x y max z max  ")
    y = core.std.Expr(clips=[r,g,b], expr=" 0.2627 x * 0.6780 y * + 0.0593 z * + ")#hardcoded for bt.2020
    satrgb1= core.std.Expr(clips=[y,max], expr="   x  y + 2 /  ")
    satrgb1=core.std.ShufflePlanes(satrgb1, planes=[0], colorfamily=vs.RGB)
    
    crgb = core.std.Expr(clips=[c], expr="  x {exposure_bias1} {exposure_bias1} * / 1 + x *  x 1 + /".format(exposure_bias1=exposure_bias1))

    satrgb2= core.std.Expr(clips=[satrgb1], expr="  x {exposure_bias1} {exposure_bias1} * / 1 + x *  x 1 + /".format(exposure_bias1=exposure_bias1)) 
      
    satrgbmult= core.std.Expr(clips=[satrgb1,satrgb2], expr="  y x /"   )    
    satrgbmult=core.std.ShufflePlanes(satrgbmult, planes=[0,0,0], colorfamily=vs.YUV)  
    satrgbmult=core.std.Limiter(satrgbmult, 0,exposure_bias1) 


    
    c=core.resize.Bicubic(clip=c, format=vs.YUV444PS, filter_param_a=0, filter_param_b=0.75,chromaloc_in_s="center",matrix_s=matrix_in_s,chromaloc_s="center", range_in_s="full", range_s="full",dither_type="none")
 
    crgb=core.resize.Bicubic(clip=crgb, format=vs.YUV444PS, filter_param_a=0, filter_param_b=0.75,chromaloc_in_s="center",matrix_s=matrix_in_s,chromaloc_s="center", range_in_s="full", range_s="full",dither_type="none")

    
      
    
    c = core.std.Expr(clips=[c], expr=["  x {exposure_bias1} {exposure_bias1} * / 1 + x *  x 1 + /".format(exposure_bias1=exposure_bias1),"",""])
    o=c

    c=core.std.Expr(clips=[o,satrgbmult], expr=[" x "," x y * "," x y * "]) 

    c=core.std.Merge(c, crgb, 0.5) 
      
    c=core.resize.Bicubic(clip=c, format=vs.RGBS, filter_param_a=0, filter_param_b=0.75,chromaloc_in_s="center",chromaloc_s="center", range_in_s="full", range_s="full",dither_type="none",  matrix_in_s=matrix_in_s)
    

    c=core.resize.Bicubic(clip=c, format=vs.RGBS, primaries_in_s="2020" , primaries_s="709",dither_type="none")
    c=core.std.Limiter(c, 0,1)
    
    c=core.std.Expr(clips=[c], expr="  x 1 2.2 / pow ")
    c=core.std.Limiter(c, 0,1)
      
    c=core.resize.Bicubic(clip=c, format=vs.YUV422P16,matrix_s="709", filter_param_a=0, filter_param_b=0.75, range_in_s="full",range_s="limited", chromaloc_in_s="center", chromaloc_s="center",dither_type="none")  
      
    return c












