#This script creates compiler specific project files and soluitons for vs2012, vs2013, vs2105, vs2017, and vs2019.
# Modify PathToICU to point to the source folder.
# FileNameSuffix, ToolVersions and CVToolSets to add new VS Compiler

import os
import shutil
import sys
import lxml.etree as ET
import re
import stat

#Change this varaible to point to the source of ICU
PathToICU = "D:\\p4\\ThirdParty\\icu\\58.2.x\\_src\\icu4c-58_2-src\\source"

#compiler specific file names
FileNameSuffix = ["_VS2012" , "_VS2013", "_VS2015", "_VS2017", "_VS2019"]

#ToolsVersion flags in solution files
ToolVersions =   ["11.0" ,    "12.0",    "14.0",    "15.0",    "16.0"]

#Visual Studio Solution Format Version
FormatVersions = ["11.00",     "12.00",  "12.00",   "12.00",    "12.00"]

#Compiler toolsets
#WARNING: You may need to adjust the toolset version in the MakeData project manually
CVToolSets =     [ "v110",     "v120",   "v140",    "v141",     "v142"]

# Update the solution files to change the tools version and referecne new compiler specific projects
def ModifySolnSettings(fName, projSuffix, ToolVersion, FormatVersion):
    with open(fName, 'r') as f:
        fileData = f.read()
    fileNameSearch = re.search(r"Format Version ([0-9.]*).*", fileData, re.IGNORECASE)
    if fileNameSearch is not None:
        newData = re.sub(r"Format Version ([0-9.]*)", r"Format Version " + FormatVersion, fileData);
    newData = re.sub('([a-zA-Z0-9_]*)\.vcxproj', r'\1'+projSuffix+'.vcxproj', newData, flags = re.M)
    with open(fName, 'w') as f:
        f.write(newData)
    
def ModifyVCXProjSettings(fName, cVersion, tVersion, projName, projSuffix):
    with open(fName, "rb+") as f:
        tree = ET.parse(f)
        root = tree.getroot()
        #Get the namespace of the root, it should be prefixed while searching for an element in tree
        namespaceGroupSearch = re.search('.*{(.*)}Project', root.tag)
        namespace = ""
        if(namespaceGroupSearch is not None):
            namespace = "{"+namespaceGroupSearch.group(1)+"}"
        ToolsVersion = root.get("ToolsVersion")
        if(ToolsVersion is not None):
            root.set("ToolsVersion", tVersion)
        for CL1 in root.iterchildren():
            strtag = CL1.tag
            #Add the project name in child PropertyGroup Label="Globals"
            Lablel = CL1.get("Label")
            Condition = CL1.get("Condition")
            if(strtag.find("PropertyGroup", 0 , len(strtag)) != -1 and Lablel is not None and Lablel.lower() == "Globals".lower()):
                ProjectName = CL1.find(namespace+"ProjectName")
                if(ProjectName is None):
                    ProjectName = ET.SubElement(CL1, "ProjectName")   
                ProjectName.text = projName
            #Add the Compiler specific tool set
            elif(strtag.find("PropertyGroup", 0 , len(strtag)) != -1 and Lablel is not None and Lablel.lower() == "Configuration".lower()):
                PlatformToolset = CL1.find(namespace+"PlatformToolset")
                if(PlatformToolset is None):
                    PlatformToolset = ET.SubElement(CL1, "PlatformToolset")
                PlatformToolset.text = cVersion
            elif(strtag.find("ItemDefinitionGroup", 0, len(strtag)) != -1 and Condition is not None):
                IsRelease = Condition.lower().find("release", 0, len(Condition))  != -1        
                #Add the variable to RuntimeLibrary
                ClCompile = CL1.find(namespace+"ClCompile")
                if ClCompile is not None:
                    RuntimeLibrary = ClCompile.find(namespace+"RuntimeLibrary")
                    if RuntimeLibrary is not None:
                        if IsRelease:
                            RuntimeLibrary.text = "$(RuntimeLibraryRelease)"
                        else:
                            RuntimeLibrary.text = "$(RuntimeLibraryDebug)"
                #Change the Vars in Link
                Link = CL1.find(namespace+"Link")
                if Link is not None:
                    GenerateDebugInformation = Link.find(namespace+"GenerateDebugInformation")
                    if(GenerateDebugInformation is None):
                        GenerateDebugInformation = ET.SubElement(Link, "GenerateDebugInformation")
                    GenerateDebugInformation.text = "true"
                    RandomizedBaseAddress = Link.find(namespace+"RandomizedBaseAddress")
                    if(RandomizedBaseAddress is None):
                        RandomizedBaseAddress = ET.SubElement(Link, "RandomizedBaseAddress")
                    RandomizedBaseAddress.text = "true"
                    AdditionalOptions = Link.find(namespace+"AdditionalOptions")
                    if(AdditionalOptions is None):
                        AdditionalOptions = ET.SubElement(Link, "AdditionalOptions")
                    AdditionalOptions.text = "/FORCE:MULTIPLE %(AdditionalOptions)"
                    OutputFile = Link.find(namespace+"OutputFile")
                    ProgramDatabaseFile = Link.find(namespace+"ProgramDatabaseFile")
                    ImportLibrary = Link.find(namespace+"ImportLibrary")
                    IsX86 = Condition.lower().find("win32") != -1
                    IsX64 = Condition.lower().find("x64") != -1
                    ver = ""
                    if IsX86:
                        ver = "_32"
                    elif IsX64:
                        ver = "_64"
                    if OutputFile is not None:
                        fileNameSearch = re.search("([a-zA-Z0-9]*)\.dll", OutputFile.text, re.IGNORECASE)
                        if fileNameSearch is not None:
                            fileName = fileNameSearch.group(1)
                            OutputFile.text = re.sub("([a-zA-Z0-9]*)\.dll", "sb"+fileName+ver+".dll", OutputFile.text)
                            if ProgramDatabaseFile is not None:
                                ProgramDatabaseFile.text = re.sub("([a-zA-Z0-9]*).pdb", "sb"+fileName+".pdb", ProgramDatabaseFile.text)
                        #lib name doesn't have versions
                        if ImportLibrary is not None:
                            libNameSearch = re.search("([a-zA-Z0-9]*)\.lib", ImportLibrary.text, re.IGNORECASE)
                            if libNameSearch is not None:
                                libFileName = libNameSearch.group(1)
                                ImportLibrary.text = re.sub("([a-zA-Z0-9]*)\.lib", "sb"+libFileName+ver+".lib", ImportLibrary.text)
                    AdditionalDependencies = Link.find(namespace+"AdditionalDependencies")
                    if AdditionalDependencies is not None:
                        AdditionalDependencies.text = re.sub("icu([a-zA-Z]*).lib", "sbicu\g<1>"+ver+".lib", AdditionalDependencies.text)
            elif(strtag.find("ItemGroup", 0, len(strtag)) != -1):
                #Change the value on the projectReference
                ProjectReferenceElems = CL1.findall(namespace+"ProjectReference")
                for i in range(len(ProjectReferenceElems)):
                    ProjectReference = ProjectReferenceElems[i]
                    if(ProjectReference is not None):
                        #update the project name specified in Include Key
                        IncludeProjectValue = ProjectReference.get("Include")
                        if(IncludeProjectValue is not None):
                            IncludeProjectSearch = re.search("([a-zA-Z0-9]*).vcxproj", IncludeProjectValue, re.IGNORECASE)
                            if IncludeProjectSearch is not None:
                                projName = IncludeProjectSearch.group(1)
                                NewincludeProjectValue = re.sub(r"([a-zA-Z0-9]*).vcxproj", projName+projSuffix+".vcxproj", IncludeProjectValue)
                                ProjectReference.set("Include", NewincludeProjectValue)
                        #Add or update the Private child
                        Private = ProjectReference.find(namespace+"Private")
                        if(Private is None):
                            Private = ET.SubElement(ProjectReference, "Private")
                        Private.text = "false"
                        #Add or update CopyLocalSatelliteAssemblies
                        CopyLocalSatelliteAssemblies = ProjectReference.find(namespace+"CopyLocalSatelliteAssemblies")
                        if(CopyLocalSatelliteAssemblies is None):
                            CopyLocalSatelliteAssemblies = ET.SubElement(ProjectReference, "CopyLocalSatelliteAssemblies")
                        CopyLocalSatelliteAssemblies.text = "false"
                        #Add or update LinkLibraryDependencies
                        LinkLibraryDependencies = ProjectReference.find(namespace+"LinkLibraryDependencies")
                        if(LinkLibraryDependencies is None):
                            LinkLibraryDependencies = ET.SubElement(ProjectReference, "LinkLibraryDependencies")
                        LinkLibraryDependencies.text = "true"
                        #Add or update UseLibraryDependencyInputs
                        UseLibraryDependencyInputs = ProjectReference.find(namespace+"UseLibraryDependencyInputs")
                        if(UseLibraryDependencyInputs is None):
                            UseLibraryDependencyInputs = ET.SubElement(ProjectReference, "UseLibraryDependencyInputs")
                        UseLibraryDependencyInputs.text = "false"
                    
                
        f.seek(0)
        f.write(ET.tostring(tree, encoding='UTF-8', xml_declaration=True))
        f.truncate()   
    
# Cleans already created _VS201[2|3|5|7].{vcxproj | sln} files    
def cleanPorjAndSolnFiles(directory):
    for root, directories, files in os.walk(directory):
        for filename in files:
            projString = re.search("^.*_VS[0-9]*\.vcxproj$", filename)
            solnString = re.search("^.*_VS[0-9]*\.sln$", filename)
            filepath = os.path.join(root, filename)
            if(projString is not None or solnString is not None):
                #print("Remvoing file :" + filepath)
                os.remove(filepath)
        
# Create Compiler specific Project and solution files
def createNewProjAndSolnFiles(directory):
    for root, directories, files in os.walk(directory):
        for filename in files:
            projString = re.search("^.*\.vcxproj$", filename)
            solnString = re.search("^.*\.sln$", filename)
            filepath = os.path.join(root, filename)
            if (solnString is not None):
                solnFileNameSearch = re.search(r"^(.*)\.sln$", filename, re.IGNORECASE)
                solnFileName = solnFileNameSearch.group(1)
                for i in range(len(FileNameSuffix)):
                    filePathVSsln = os.path.join(root,solnFileName) + FileNameSuffix[i] + ".sln"
                    shutil.copy2(filepath, filePathVSsln)
                    os.chmod( filePathVSsln, stat.S_IWRITE)
                    #print("Created Sln : " + filePathVSsln)
                    ModifySolnSettings(filePathVSsln, FileNameSuffix[i], ToolVersions[i], FormatVersions[i])
            elif (projString is not None):
                vcxFileNameSearch = re.search("^(.*)\.vcxproj$", filename, re.IGNORECASE)
                vcxFileName = vcxFileNameSearch.group(1)
                for i in range(len(FileNameSuffix)):
                    filePathVSvcx = os.path.join(root,vcxFileName) + FileNameSuffix[i] + ".vcxproj"
                    shutil.copy2(filepath, filePathVSvcx)
                    os.chmod( filePathVSvcx, stat.S_IWRITE)
                    #print("Created Proj: " + filePathVSvcx)
                    ModifyVCXProjSettings(filePathVSvcx, CVToolSets[i], ToolVersions[i], vcxFileName, FileNameSuffix[i])
                
def buildICU_VS(PathToICU):
    cleanPorjAndSolnFiles(PathToICU)
    createNewProjAndSolnFiles(PathToICU)
    

buildICU_VS(PathToICU)
