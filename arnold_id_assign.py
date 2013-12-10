### DEscription ###
## This script is to create AOV pass system like mental ray contribution passes
## This script is still deving/improving
## really welcome anyone can give/ mail me any comments and suggestions
## Thanks! :)
## Kenzie Chen | kenziec@themill.com  


### Limits ###
## Due to use aiUserData, the shape node has some custome attributes
## so, there are 2 limits as below   
## 01. When update new reference model, those custom attributes are gone!
## 02. when using deformer, there is a new shape node generates, so siUserData will ignore the old shape node
## which has cutome attributes.



## load lib
import pymel.core as pm
import sys
import copy
import math

# check if current render is Arnold
if( pm.getAttr( 'defaultRenderGlobals.currentRenderer' ) != 'arnold' ):
   pm.confirmDialog( t="Error", message="Please use Arnold render", icon='critical' )
   sys.exit( "Please use Arnold render!" )
                  
import mtoa.aovs as aovs

# declare ui 
uiLayout = {}

# declaire global variable
prefixAOV = 'mtoa_constant_'
isProgress = False
sel = []

    
''' =============== sub-function =============== '''
## check if any object is seleted
def isSelEmpty(*args):
    ## access the global "sel"
    global sel
    
    sel = pm.ls( sl=True, dag=True, type='shape' )
    print "sel", sel      
    if( sel == [] ):
       pm.confirmDialog(t="Error", message="No Object is selected", icon='critical')
       return 0
    
    return 1 

    
## check is selection has unsupport type
def isObjType(*args):
    tmpList = [ o.getParent() for o in sel if not(pm.nodeType(o) == 'mesh' or pm.nodeType(o) == 'nurbsSurface') ]
    
    tmpStr = ''
    for s in tmpList:
        tmpStr = tmpStr + s + ','
            
    if( len(tmpList) > 0 ):
        pm.confirmDialog(t="Error", message= tmpStr + " are not mesh or nurbsSurface", icon='critical')
        return 0
    
    return 1


## add Color/ String attributes
def addUserAttr( obj, attrType ):
    if( attrType == 'float3' ):
       pm.addAttr( obj, longName=(prefixAOV+'idcolor'), niceName='idcolor', usedAsColor=True, attributeType='float3' )
       pm.addAttr( obj, longName=(prefixAOV+'r'), attributeType='float', parent=(prefixAOV+'idcolor') )
       pm.addAttr( obj, longName=(prefixAOV+'g'), attributeType='float', parent=(prefixAOV+'idcolor') )
       pm.addAttr( obj, longName=(prefixAOV+'b'), attributeType='float', parent=(prefixAOV+'idcolor') )
    elif( attrType == 'string' ):
      pm.addAttr( obj, longName=(prefixAOV+'Id'), niceName='id_name', dataType='string' )
      
    return 1

          
## Creates AOV render pass
def addAOV( name ): 
    aovName = 'id_' + name
    aovs.AOVInterface().addAOV( aovName )
    
    aovNode = aovs.AOVInterface().getAOVNode( aovName )
    pm.addAttr( aovNode, longName='isID', niceName='ai_ID', attributeType='bool', defaultValue=1 )
    aovNode.setAttr( 'isID', lock=True )
          
    return 1
        
    
## add AOV Attribute for objects
def doAddAOVAttr(*args):
    if( ( isSelEmpty() and isObjType() ) == False ):
        return 0
        
    aovName = pm.textFieldButtonGrp( 'txtBtnAddAttr', query=True, text=True )
    if( len(aovName) == 0 ):
        pm.confirmDialog( t='warning', message='AOV name field is empty!', icon='warning' )
        return 0
    
    for obj in sel:                  
       if( not( obj.hasAttr(prefixAOV+'Id') ) ):
           addUserAttr( obj, 'string' )
                   
       # add AOV name as Attribute
       pm.PyNode( obj + '.' + prefixAOV + 'Id' ).set( 'id_'+aovName )
    
       # skip loop if the input textfield is empty
       if( len(aovName) == 0 ): continue
            
       # add AOV render pass
       # check if AOV already existing
       if( len( pm.ls('aiAOV_id_'+aovName) ) == 0 ):
           addAOV( aovName )
           
    return 1


def doAddColorAttr( inColor ): 
    if( ( isSelEmpty() and isObjType() ) == False ):
        return 0
        
    for obj in sel:
       if( not( obj.hasAttr(prefixAOV+'idcolor') ) ):
           addUserAttr( obj, 'float3' )                       
       # assign color
       pm.PyNode( obj + '.' + prefixAOV + 'idcolor' ).set( inColor )
              
    return 1
   
   
## delete custom mtoa* attributes
def doDelAttrAOV(*args):
    if( isSelEmpty() and isObjType() == False ):
        return 0
    
    for obj in sel:
        if( obj.hasAttr(prefixAOV+'Id') ):
            pm.deleteAttr( obj, attribute=prefixAOV+'Id' )
        if( obj.hasAttr(prefixAOV+'idcolor') ):
            pm.deleteAttr( obj, attribute=prefixAOV+'idcolor' )
            
    return 1


## delete unused AOVs
def doDelEmptyAOVs(*args):
    updateAOVStrAttr()
    
    attr_color = [ 'obj_R', 'obj_G', 'obj_B', 'obj_W' ]
    sceneAOVs = aovs.AOVInterface().getAOVNodes(names=True)
    # filter AOV
    id_aov_sets = [ node for name, node in sceneAOVs if name.find('id_') == 0 ]
     
    for aov in id_aov_sets:
        count = 0
        for attr in attr_color:
            if( pm.PyNode(aov).hasAttr(attr) ):
                if( len(pm.PyNode(aov + '.' + attr).get()) == 0 ):
                    count += 1
                                                      
        if count == 4:
            pm.delete(aov)
            doUpdateScnAOV(1)
            
    return 1


## update/ collect each AOVs containing objects list
def updateAOVStrAttr(*args):
    # custom Attr
    strAttr_obj_R = 'obj_R'
    strAttr_obj_G = 'obj_G'
    strAttr_obj_B = 'obj_B'
    strAttr_obj_W = 'obj_W'
    
    sceneAOVs = aovs.AOVInterface().getAOVNodes(names=True)
    
    # filter AOV
    id_aov_sets = [ node for name, node in sceneAOVs if( name.find('id_') == 0 and node.hasAttr('isID') ) ]
    
    # loop each AOV to add custom Attr
    for aov in id_aov_sets:
        if( not( pm.PyNode(aov).hasAttr(strAttr_obj_R) ) ):
            pm.addAttr( aov, longName=strAttr_obj_R, niceName='R', dataType='string' )
            
        if( not( pm.PyNode(aov).hasAttr(strAttr_obj_G) ) ):
            pm.addAttr( aov, longName=strAttr_obj_G, niceName='G', dataType='string' )
            
        if( not( pm.PyNode(aov).hasAttr(strAttr_obj_B) ) ):
            pm.addAttr( aov, longName=strAttr_obj_B, niceName='B', dataType='string' )
            
        if( not( pm.PyNode(aov).hasAttr(strAttr_obj_W) ) ):
            pm.addAttr( aov, longName=strAttr_obj_W, niceName='W', dataType='string' )
                                                     
        # initialize                            
        pm.PyNode(aov+'.'+strAttr_obj_R).set('')
        pm.PyNode(aov+'.'+strAttr_obj_G).set('')
        pm.PyNode(aov+'.'+strAttr_obj_B).set('')
        pm.PyNode(aov+'.'+strAttr_obj_W).set('')
        
    # collect mesh in scene           
    listMesh = pm.ls(type='mesh')
    if( len(listMesh) == 0 ): return "no mesh in scene"
      
    maxValue = len(listMesh)
    global isProgress
    
    pm.progressWindow( title='AOV Update Calculation', progress=0, maxValue=maxValue , isInterruptable=True, status='calculating: 0%' )
    isProgress = True     
    for amount, mesh in enumerate(listMesh, 0):
        pm.progressWindow( edit=True, progress=amount, status=('calculating: ' + str( math.ceil(100 * amount/ maxValue) ) + '%') )
        if pm.progressWindow( query=True, isCancelled=True ) :
            break
        
        ## test if obj has both id and idcolor attrs ##
        if( mesh.hasAttr('mtoa_constant_Id') and mesh.hasAttr('mtoa_constant_idcolor') ):
            print mesh
            idName = mesh.mtoa_constant_Id.get()
            idColor = mesh.mtoa_constant_idcolor.get()
            
            if( idColor == (1.0, 0.0, 0.0) ):
                AOV_attr_obj = 'aiAOV_' + idName + '.' + strAttr_obj_R
                
            if( idColor == (0.0, 1.0, 0.0) ):
                AOV_attr_obj = 'aiAOV_' + idName + '.' + strAttr_obj_G
                
            if( idColor == (0.0, 0.0, 1.0) ):
                AOV_attr_obj = 'aiAOV_' + idName + '.' + strAttr_obj_B
                
            if( idColor == (1.0, 1.0, 1.0) ):
                AOV_attr_obj = 'aiAOV_' + idName + '.' + strAttr_obj_W
            
            # test if shape's aov is not existing in scene AOV
            if( len( pm.ls( 'aiAOV_' + idName ) ) == 0 ):
                continue
            
            # write to object_list Attr     
            pm.PyNode(AOV_attr_obj).set( pm.PyNode(AOV_attr_obj).get() + mesh.getParent() + ';' )

    
    pm.progressWindow( endProgress=1 )
    isProgress = False       
    return 1
          

def doStopUpdateAOV(*args):
    if isProgress:
        pm.progressWindow(endProgress=1)
    return 1


## update scene id/ AOV
def doUpdateScnAOV(type, *args):
    # first, update string attr in each AOV
    if type == 0:
        updateAOVStrAttr()
    
    # next, update AOV list
    AOVList = []
    sceneAOVs = aovs.AOVInterface().getAOVNodes(names=True)
    for aovName, aovNode in sceneAOVs:
        if( aovName.find('id_') == 0 and aovNode.hasAttr('isID') ):
            AOVList.append( str(aovName) )
    
    enumUIParent = pm.optionMenu( 'enumAOVList', q=True, parent=True )
    pm.deleteUI('enumAOVList')
        
    pm.optionMenu( 'enumAOVList', bgc=[0.2, 0.2, 0.2], label="AOVs: ", width=120, parent=enumUIParent )
    for aov in AOVList:
        pm.menuItem( aov )

    return 1
    

def doSelObjInAOV(*args):
    curr_aov = pm.optionMenu( 'enumAOVList', q=True, value=True )

    if( curr_aov == None ): return 0
    
    # [:-1] means remove last string, an empty space   
    pm.select(cl=True)

    if( pm.checkBox( 'chk_R', query=True, v=True ) ):
        pm.select( pm.PyNode('aiAOV_'+curr_aov).obj_R.get().split(';')[:-1], add=True )
        
    if( pm.checkBox( 'chk_G', query=True, v=True ) ):
        pm.select( pm.PyNode('aiAOV_'+curr_aov).obj_G.get().split(';')[:-1], add=True )
                
    if( pm.checkBox( 'chk_B', query=True, v=True ) ):
        pm.select( pm.PyNode('aiAOV_'+curr_aov).obj_B.get().split(';')[:-1], add=True )
                
    if( pm.checkBox( 'chk_W', query=True, v=True ) ):
        pm.select( pm.PyNode('aiAOV_'+curr_aov).obj_W.get().split(';')[:-1], add=True )
        
    return 1
            
                        
def doDelAOV(*args):
    curr_aov = pm.optionMenu( 'enumAOVList', q=True, value=True )
    if curr_aov == None: return 0
    
    aovs.AOVInterface().removeAOVs(curr_aov)
    doUpdateScnAOV(1)
    
    return 1;


## rebuild object Attr from AOVs
## when updateing model assets
def doRebuildObjData(*args):
    global sel
    
    color_tag = [ ['obj_R', (1, 0, 0)], ['obj_G', (0, 1, 0)], ['obj_B', (0, 0, 1)], ['obj_W', (1, 1, 1)] ]
    sceneAOVs = aovs.AOVInterface().getAOVNodes(names=True)
    
    id_AOVs = [ ( name, node ) for name, node in sceneAOVs if( name.find('id_') == 0 and node.hasAttr('isID') ) ]
    
    # for each AOV
    #     for r,g,b,w Attr
    #        get objects/ color info
    #            copy info to new objects  
    miss_obj = []
    for aov_name, aov_node in id_AOVs:
        for attr, val in color_tag:
            print '%s: %s, %s' % (aov_name, attr, val)
            list_obj = pm.PyNode( aov_node + "." + attr ).get().split(';')[:-1]
            if len(list_obj) == 0: continue
            
            # copy ID & idcolor Attr from AOV node to Obj
            for obj in list_obj:
                # test obj in lsit if not existing
                if len( pm.ls(obj) ) == 0:
                    print 'obj not match: ', obj
                    miss_obj.append(obj)
                    continue
                
                # test if obj has ID Attr
                if not obj.hasAttr(prefixAOV+'Id'):
                    addUserAttr( obj.getShape(), 'string' )
                    
                # test if obj has idcolor Attr    
                if not obj.hasAttr(prefixAOV+'idcolor'):
                    addUserAttr( obj.getShape(), 'float3' )
            
                pm.PyNode( obj + '.' + prefixAOV + 'Id' ).set( aov_name )        
                pm.PyNode( obj + '.' + prefixAOV + 'idcolor' ).set( val )
                

    pm.confirmDialog( t='Complete!', message='Rebuild AOV --> Obj is done!', b=['OK'], icon='information' )
    pm.confirmDialog( t='Objects Missing!', message=('Original Objects Missing Target: \n======================\n%s' % "\n".join(miss_obj) ), b=['OK'], icon='critical' )                                         
            

## create shading network
def doIDShdNetwork(*args):
    ## check if the shading network is existing
    shdName = 'idSetup'

    if( len( pm.ls(shdName + "_SHD") ) ) != 0:
        pm.confirmDialog(t="Warning", message="The shader has been existed!", icon='warning')
        return 0
        
    # aiUserDataColor
    dataColor = pm.shadingNode('aiUserDataColor', asUtility=True, name=shdName+'DataColor')
    dataColor.colorAttrName.set('idcolor')
    
    # aiUserDataString
    dataString = pm.shadingNode('aiUserDataString', asUtility=True, name=shdName+'DataString')
    dataString.stringAttrName.set('Id')
    
    # aiWriteColor
    writeColor = pm.shadingNode('aiWriteColor', asUtility=True, name=shdName+'WriteColor')
    
    # aiUtility
    aiIDShd = pm.shadingNode('aiUtility', asShader=True, name=shdName+'_SHD')
    aiIDShd.shadeMode.set(2)
    
    # connections
    dataColor.outColor >> writeColor.input
    dataString.outValue >> writeColor.aovName
    writeColor.outColor >> aiIDShd.color     
          

          
''' ===============  main function =============== ''' 
def main():
    ## check if the current renderer is Arnold
    global sel   
    if( pm.window('ArnoldAOVSetup', exists=True) ):
       pm.deleteUI('ArnoldAOVSetup')    
  
    uiLayout['window'] = pm.window('ArnoldAOVSetup', menuBar=True, title='Setup Arnold Tech IDs', sizeable=False, h=400, w=250)
    uiLayout['mainLayout'] = pm.columnLayout( columnAlign='left', columnAttach=['left', 0] )
    
    
    ### NO.1 column
    uiLayout['ui_sub1'] = pm.frameLayout( label='01. AOV name setup', width=250, bgc=[0.2, 0.2, 0.2], cl=False, cll=True, borderStyle='in', p=uiLayout['mainLayout'] )
    
    pm.text( label='--- Input AOV name for selected objects ---', align='center', bgc=[0.1, 0.1, 0.1], parent=uiLayout['ui_sub1'] )
    
    ## AOV name/ Attribute assign
    uiLayout['ui_sub1a'] = pm.rowLayout( nc=4, p=uiLayout['ui_sub1'] )
    pm.text( label='AOV name:', parent=uiLayout['ui_sub1a'] )
    pm.textField( text='id_', bgc=[0.4, 0, 0 ], editable=False, width=25, parent=uiLayout['ui_sub1a'] )
    pm.text( label='+', parent=uiLayout['ui_sub1a'] )   
    uiLayout['addObjAttr'] = pm.textFieldButtonGrp( 'txtBtnAddAttr', label='', text='', buttonLabel='  Assign  ', cw3=[0, 80, 0], buttonCommand=doAddAOVAttr, parent=uiLayout['ui_sub1a'] )        
    
    pm.separator(h=8, w=250, style='single', p=uiLayout['mainLayout'])
     

    ### NO.2 column   
    uiLayout['ui_sub2'] = pm.frameLayout( label='02. AOV color setup', width=250, bgc=[0.2, 0.2, 0.2], cl=True, cll=True, borderStyle='in', p=uiLayout['mainLayout'] )
    
    pm.text( label='--- Pick AOV color for selected objects ---', align='center', bgc=[0.1, 0.1, 0.1], parent=uiLayout['ui_sub2'] )

    uiLayout['ui_sub2_color'] = pm.rowColumnLayout( w=250, nc=4, cw=[(1,60), (2,60), (3,60), (4,60)], parent=uiLayout['ui_sub2'] )
    pm.button(l='Red', ebg=True, bgc=[1, 0, 0], c=lambda *args:doAddColorAttr( [1, 0, 0] ), parent=uiLayout['ui_sub2_color'])
    pm.button( label='Green', ebg=True, bgc=[0, 1, 0], c=lambda *args:doAddColorAttr( [0, 1, 0] ), parent=uiLayout['ui_sub2_color'] )
    pm.button( label='Blue', ebg=True, bgc=[0, 0, 1], c=lambda *args:doAddColorAttr( [0, 0, 1] ), parent=uiLayout['ui_sub2_color'] )
    pm.button( label='White', ebg=True, bgc=[1, 1, 1], c=lambda *args:doAddColorAttr( [1, 1, 1] ), parent=uiLayout['ui_sub2_color'] )
    
    pm.separator(h=8, w=250, style='single', p=uiLayout['mainLayout'])

   
    ### NO.3 column
    uiLayout['ui_sub3'] = pm.frameLayout( label='03. Shader setup', width=250, bgc=[0.2, 0.2, 0.2], cl=True, cll=True, borderStyle='in', p=uiLayout['mainLayout'] )
    pm.text( label='--- Create Shading Network ---', align='center', bgc=[0.1, 0.1, 0.1], parent=uiLayout['ui_sub3'] )
    uiLayout['ui_sub3_btn'] = pm.rowColumnLayout( w=250, nc=2, cw=[(1,120), (2,120)], parent=uiLayout['ui_sub3'] )
    pm.button( label=' Create !', ebg=True, c=doIDShdNetwork, parent=uiLayout['ui_sub3_btn'] )
    pm.button( label=' Assign !', ebg=True, en=False, parent=uiLayout['ui_sub3_btn'] )
    
    pm.separator(h=8, w=250, style='single', p=uiLayout['mainLayout'])
    
    
    ### NO.4 column
    uiLayout['ui_sub_4'] = pm.frameLayout( label='* Advance Control *', bgc=[0.3, 0.3, 0.1], width=250, cl=True, cll=True, borderStyle='in', p=uiLayout['mainLayout'] )
    pm.text( label='--- AOVs & Objects Attr operation ---', align='center', bgc=[0.1, 0.1, 0.1], parent=uiLayout['ui_sub_4'] )
    
    uiLayout['ui_sub_4_aov'] = pm.frameLayout( label='** AOVs Control', bgc=[0.25, 0.2, 0.2], width=300, cl=True, cll=True, borderStyle='in', p=uiLayout['ui_sub_4'] )  
    uiLayout['ui_sub_4_aov_1'] = pm.rowLayout( nc=3, p=uiLayout['ui_sub_4_aov'] )
        
    ## setup enum list
    pm.button( label=' Update AOV ', ebg=True, bgc=[0.5, 0.5, 0.2], c=lambda *args:doUpdateScnAOV(0), parent=uiLayout['ui_sub_4_aov_1'] )
    pm.button( label=' stop ', ebg=True, bgc=[0.5, 0.2, 0.2], c=doStopUpdateAOV, parent=uiLayout['ui_sub_4_aov_1'] ) 
    pm.optionMenu( 'enumAOVList', label="AOVs: ", width=120, bgc=[0.2, 0.2, 0.2], parent=uiLayout['ui_sub_4_aov_1'] )

            
    uiLayout['ui_sub_4_aov_2'] = pm.rowLayout( nc=5, cw=[(1,90), (2,35), (3,35), (4,35), (5,35)], p=uiLayout['ui_sub_4_aov'] )
    pm.button( label=' Select Objects ', ebg=True, c=doSelObjInAOV, parent=uiLayout['ui_sub_4_aov_2'] )
    pm.checkBox( 'chk_R', label='R', v=True, ebg=True, bgc=[1, 0, 0] )
    pm.checkBox( 'chk_G', label='G', v=True, ebg=True, bgc=[0, 1, 0] )
    pm.checkBox( 'chk_B', label='B', v=True, ebg=True, bgc=[0, 0, 1] )
    pm.checkBox( 'chk_W', label='W', v=True, ebg=True, bgc=[1, 1, 1] )
    
    uiLayout['ui_sub_4_aov_3'] = pm.rowLayout( nc=3, cw=[(1,50), (2,100), (3,100)], p=uiLayout['ui_sub_4_aov'] )
    
    pm.button( label=' Del AOV ', c=doDelAOV, bgc=[0.7, 0, 0], parent=uiLayout['ui_sub_4_aov_3'] )
    
    ## delete buttons group ##
    pm.button( label=' Del Empty AOVs! ', ebg=True, c=doDelEmptyAOVs, parent=uiLayout['ui_sub_4_aov_3'] )
    pm.button( label=' Del Attributes! ', ebg=True, c=doDelAttrAOV, parent=uiLayout['ui_sub_4_aov_3'] )
    
    ## DATA rebuild
    ## to copy shape attributes to new update model assets 
    '''uiLayout['ui_sub_4_data'] = pm.frameLayout( label='** Attr Rebuild', bgc=[0.2, 0.25, 0.2], width=300, cl=True, cll=True, borderStyle='in', p=uiLayout['ui_sub_4'] )
    uiLayout['ui_sub_4_data_1'] = pm.rowColumnLayout( w=250, nc=2, cw=[(1,120), (2,120)], parent=uiLayout['ui_sub_4_data'] )
    pm.button( label=' Rebuild from AOVs !', ebg=True, c=doRebuildObjData, parent=uiLayout['ui_sub_4_data_1'] )
    '''
    
    
    
    #print uiLayout
    pm.showWindow( uiLayout['window'] )
    
main()
