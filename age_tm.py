#bt2390_ictcp




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
    width_n=width
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
   
    I=core.std.Limiter(I, 0,lw,planes=[0])      
   

   

   


     
    
    





    c=core.resize.Bicubic(clip=c, format=vs.RGBS, filter_param_a=0, filter_param_b=0.75,chromaloc_in_s="center", chromaloc_s="center", range_in_s="full", range_s="full",dither_type="none", matrix_in_s="2020ncl")
    c=core.std.Limiter(c, 0,lw) 
 
    cs=core.resize.Bicubic(clip=c, format=vs.RGBS, transfer_in_s=transfer_in_s, transfer_s="linear",dither_type="none", nominal_luminance=source_peak)
 
 
 
    cs = core.std.Expr(clips=[cs], expr="x {exposure_bias1} *".format(exposure_bias1=exposure_bias1)) 
 
 
    
    r=core.std.ShufflePlanes(cs, planes=[0], colorfamily=vs.GRAY)
    g=core.std.ShufflePlanes(cs, planes=[1], colorfamily=vs.GRAY)
    b=core.std.ShufflePlanes(cs, planes=[2], colorfamily=vs.GRAY)
    max = core.std.Expr(clips=[r,g,b], expr="x y max z max") 
    min = core.std.Expr(clips=[r,g,b], expr="x y min z min")
    sat = core.std.Expr(clips=[max,min], expr="x y -")        
    l = core.std.Expr(clips=[r,g,b], expr="0.2627 x * 0.6780 y * + 0.0593 z * +") 
    l=  core.std.ShufflePlanes(clips=[l,l,l], planes=[0,0,0], colorfamily=vs.RGB)      

    saturation_mult1=core.std.Expr(clips=[sat], expr=" x 1 -     {exposure_bias1} 1 -  / ".format(exposure_bias1=exposure_bias1))
    saturation_mult1=core.std.Limiter(saturation_mult1, 0,1)    
    
    c1=core.std.MaskedMerge(cs, l, saturation_mult1)
    c=core.std.Merge(cs, c1, 0.5)


    c = core.std.Expr(clips=[c], expr="x {exposure_bias1} /".format(exposure_bias1=exposure_bias1)) 

    c=core.resize.Bicubic(clip=c, format=vs.RGBS, transfer_in_s="linear", transfer_s=transfer_in_s,dither_type="none", nominal_luminance=source_peak,cpu_type=None)
 
 
 
 
        
    e1=core.std.Expr(clips=[c], expr="x  {lw} /".format(lw=lw))
    t = core.std.Expr(clips=[e1], expr="x {ks} - 1 {ks} - / ".format(ks=ks))    
    p = core.std.Expr(clips=[t], expr="  2 x 3 pow *  3 x 2 pow   * - 1 + {ks} * 1 {ks} - x 3 pow  2 x 2 pow *    -   x  + * + -2 x 3 pow  *  3 x 2 pow  *  + {maxlum} * +".format(ks=ks,maxlum=maxlum))    
    e2=core.std.Expr(clips=[e1,p], expr="x {ks} < x y ? ".format(ks=ks))
    crgb=core.std.Expr(clips=[e2], expr="x  {lw} * ".format(lw=lw))   
    crgb=core.std.Limiter(crgb, 0,1)  

    rgb=crgb
    
    crgb=core.resize.Bicubic(clip=crgb, format=vs.YUV444PS, filter_param_a=0, filter_param_b=0.75,chromaloc_in_s="center", transfer_in_s=transfer_in_s, transfer_s=transfer_in_s,chromaloc_s="center", range_in_s="full", range_s="full",dither_type="none", nominal_luminance=target_nits, matrix_s="ictcp",cpu_type=None)


    Irgb=core.std.ShufflePlanes(crgb, planes=[0], colorfamily=vs.GRAY)


    saturation_mult1=core.std.Expr(clips=[saturation_mult1], expr=" 1 x - ".format(lw=lw,lmax=lmax))

    saturation_mult=core.std.Expr(clips=[I,Irgb], expr=" y x  / ")
    saturation_mult=core.std.Limiter(saturation_mult, 0,1)

    ct=core.std.Expr(clips=[ct,saturation_mult1], expr=" x y * ")
    cp=core.std.Expr(clips=[cp,saturation_mult1], expr="  x y *  ") 
   
    ct=core.std.Expr(clips=[ct,saturation_mult], expr=" x y * ")
    cp=core.std.Expr(clips=[cp,saturation_mult], expr="  x y *  ")    

    c_ictcp=core.std.ShufflePlanes(clips=[Irgb,ct,cp], planes=[0,0,0], colorfamily=vs.YUV)









    c_ictcp=core.resize.Bicubic(clip=c_ictcp, format=vs.RGBS, filter_param_a=0, filter_param_b=0.75,chromaloc_in_s="center", transfer_in_s=transfer_in_s,transfer_s=transfer_in_s,chromaloc_s="center", range_in_s="full", range_s="full",dither_type="none", nominal_luminance=target_nits, matrix_in_s="ictcp",cpu_type=None)

    c_ictcp=core.std.Limiter(c_ictcp, 0,1)
   
  

    c=core.std.Merge(c_ictcp, rgb, 0.75)
    c=core.std.Limiter(c, 0,1)
 

      
   
    c=core.resize.Bicubic(clip=c, format=vs.RGBS, transfer_in_s=transfer_in_s, transfer_s="linear",dither_type="none", nominal_luminance=target_nits)
    

  
    c=core.resize.Bicubic(clip=c, format=vs.RGBS, primaries_in_s=primaries, primaries_s="709",dither_type="none")
    c=core.std.Limiter(c, 0,1)


    c = core.std.Expr(clips=[c], expr=" x 1 2.2 / pow")
        
#    c=core.resize.Bicubic(clip=c, format=vs.RGBS, transfer_in_s="linear", transfer_s="709",dither_type="none")
    c=core.std.Limiter(c, 0,1)

    c=core.resize.Bicubic(clip=c, format=vs.YUV422P16,matrix_s="709", filter_param_a=0, filter_param_b=0.75, range_in_s="full",range_s="limited", chromaloc_in_s="center", chromaloc_s="center",dither_type="none")  
      
    return c
   










