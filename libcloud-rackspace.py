###
## TODO: Change volume attach to node with matching name
###

from dateutil.parser import parse
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from libcloud.compute.deployment import MultiStepDeployment, SSHKeyDeployment

import os.path

uinp = 0
inventoryFilename = 'rackspace.inventory'
statuses = {
    0: 'Active',
    3: 'Building'
}

# Prodiver
cls = get_driver(Provider.RACKSPACE)

# Cloud specific information
USER = 'username'
API_KEY = 'apikey'
RS_REGION = 'region'
SSH_USERNAME = 'root'
BLOCK_DEVICE = '/dev/xvdb'

# List nodes
def listNodes():
    print '\nTASK: List Nodes ***\n'
    print '** Connecting to the cloud **\n'

    # Get Cloud
    driver = cls(USER, API_KEY, region=RS_REGION)

    print '** Gathering the cloud information **\n'

    # Get node list
    nodes = driver.list_nodes()

    print '** Listing node information **\n'

    # Print node information
    for node in nodes:
        stateText = 'Unknown'
        createdDate = parse(node.extra['created'])
        updatedDate = parse(node.extra['updated'])
        
        if node.state in statuses:
            stateText = statuses[node.state] 

        print 'Name:       ', node.name
        print 'State:      ', stateText
        print 'Public IPs: ', node.public_ips
        print 'Private IPs:', node.private_ips
        print 'Created:    ', createdDate.strftime('%d.%m.%Y %H:%M:%S')
        print 'Updated:    ', updatedDate.strftime('%d.%m.%Y %H:%M:%S')
        print ''
    
    if len(nodes) == 0:
        print '# No nodes\n'
        
    else:
        print '#', len(nodes),'nodes\n'
    
    return
# List nodes

# Create Nodes
def createNodes():
    print '\nTASK: Create Nodes ***\n'
    
    print '** Connecting to the cloud **\n'

    uinp = 'y'
    runCount = 0
    
    # Get Cloud
    driver = cls(USER, API_KEY, region='iad')
    
    print '** Gathering the cloud information **\n'
    
    # Get existing nodes
    nodes = driver.list_nodes()
    
    if len(nodes) > 0:
        print 'You already have', len(nodes), 'nodes. Are you sure you want to create more? (y/n)'
        uinp = raw_input('> ')
    
    if uinp in ('y', 'Y'):
        # Get available instance types
        sizes = driver.list_sizes()

        # Get available images
        images = driver.list_images()

        # Set instance type
        size = [s for s in sizes if s.id == '3'][0] # id 3: name=1GB Standard Instance, ram=1024 MB, disk=40 GB, bandwidth=None, price=0.06 $/hr

        # Set image
        image = [i for i in images if 'Debian 7' in i.name][0]

        # Get SSH public key
        sshPubKey = SSHKeyDeployment(open(os.path.expanduser("~/.ssh/id_rsa.pub")).read())
        
        # Set Deployment steps
        msd = MultiStepDeployment([sshPubKey])
        
        # Names for nodes
        nodeNames = [ 'rackspace-loadbalancer', 'rackspace-mysql-01', 'rackspace-mysql-02', 'rackspace-nfs-01', 'rackspace-nfs-02', 'rackspace-drupal-01', 'rackspace-drupal-02' ]
        
        print '** Creating nodes **\n'

        # Create instances
        for (i, nodeName) in enumerate(nodeNames):
            run = True
            
            for exNode in nodes:
                if nodeName == exNode.name and exNode.state == 0:
                    run = False
            
            if run == True:
                print ('- Creating node #%d' % (i + 1))
                node = driver.deploy_node(name=nodeName, size=size, image=image, deploy=msd)
                print '- Inject SSH Key'
                print ('# Created node %s' % nodeName)
                print '  UUID: ', node.uuid
                print '  Name: ', node.name
                print '  State:', node.state
                print ''
                runCount += 1
                
            else:
                print '# Skipped', nodeName,'; already running\n'
                

        print '# Created', runCount, 'nodes\n'
        
        if len(nodeNames) > runCount:
            '# Skipped ', (nodeNames - runCount), ' nodes\n'
        
    else:
        print '# Task cancelled\n'
    
    return
# Create Nodes

# List volumes
def listVolumes():
    print '\nTASK: List Volumes ***\n'
    
    print '** Connecting to the cloud **\n'

    # Get Cloud
    driver = cls(USER, API_KEY, region='iad')

    print '** Gathering the cloud information **\n'

    # Get volume list
    volumes = driver.list_volumes()
    
    # Get node list
    nodes = driver.list_nodes()
    
    print '** Listing node information **\n'

    # Print node information
    for volume in volumes:
        attached = 'N/A'
        mountPoint = 'N/A'
        
        if len(volume.extra['attachments']) > 0:
            for node in nodes:
                if volume.extra['attachments'][0]['serverId'] in node.id:
                    attached = node.name
            
            mountPoint = volume.extra['attachments'][0]['device']
        
        print 'ID:      ', volume.id
        print 'Name:    ', volume.extra['description']
        print 'Size:    ', volume.size, 'GB'
        print 'Mount:   ', mountPoint
        print 'Attached:', attached
        print ''
    
    if len(volumes) == 0:
        print '# No volumes\n'
        
    else:
        print '#', len(volumes),'volumes\n'
    
    return
# List volumes

# Create volumes
def createVolumes():
    print '\nTASK: Create Volumes ***\n'
    
    print '** Connecting to the cloud **\n'

    uinp = 'y'
    runCount = 0
    
    # Get Cloud
    driver = cls(USER, API_KEY, region='iad')

    print '** Gathering the cloud information **\n'

    # Get volume list
    volumes = driver.list_volumes()

    if len(volumes) > 0:
        print 'You already have', len(volumes), 'volumes. Are you sure you want to create more? (y/n)'
        uinp = raw_input('> ')
    
    if uinp in ('y', 'Y'):
        # Volume names
        volumeNames = [ 'vol-nfs-01', 'vol-nfs-02', 'vol-mysql-01', 'vol-mysql-02' ]
        volumeSize = 100

        # Create volumes
        print '** Creating volumes **\n'

        # Create instances
        for (i, volumeName) in enumerate(volumeNames):
            run = True
            
            for exVolume in volumes:
                if volumeName == exVolume.extra['description']:
                    run = False
            
            if run == True:
                print ('- Creating volume #%d' % (i + 1))
                volume = driver.create_volume(volumeSize, volumeName)
                print ('- Created volume %s' % volumeName)
                print ''
                
            else:
                print '# Skipped', volumeName,'- already exists\n'

        print '# Created', len(volumeNames), 'volumes\n'
        
        if len(volumeNames) > runCount:
            '# Skipped', (len(volumeNames) - runCount), 'volumes\n'
        
    else:
        print '# Task cancelled\n'
        
    return
# Create volumes

# Attach volumes
def attachVolumes():
    print '\nTASK: Attach Volumes ***\n'
    
    print '** Connecting to the cloud **\n'

    attachCount = 0
    
    nodeVolumeAttachList = [ 'mysql', 'nfs' ]
    nodesForVolumes = []
    
    # Get Cloud
    driver = cls(USER, API_KEY, region='iad')

    print '** Gathering the cloud information **\n'

    # Get volume list
    volumes = driver.list_volumes()
    
    # Get node list
    nodes = driver.list_nodes()
    
    print '** Selecting nodes **\n'
    
    for nvai in nodeVolumeAttachList:
        for node in nodes:
            if nvai in node.name:
                nodesForVolumes.append(node)
                
    if len(volumes) == 4 and len(nodesForVolumes) == 4:
        print '** Attaching volumes **\n'
        
        for (i, node) in enumerate(nodesForVolumes):
            if len(volumes[i].extra['attachments']) == 0:
                print '- Attach #', (i + 1) ,'volume'
                driver.attach_volume(node, volumes[i], BLOCK_DEVICE)
                print '# Attached volume', volumes[i].id, 'to node', node.name
                print ''
                attachCount = +1
            
            else:
                print '# Skipped', volumes[i].extra['description'],'- already attached\n'
            
        print '# Attached', attachCount, 'volumes\n'
        
        if len(volumes) > attachCount:
            '# Skipped', (len(volumes) - attachCount), 'nodes\n'
        
    else:
        print 'Volume count', len(volumes), 'does not match to node count', len(nodeVolumes), '\n'
    
    return
# Attach volumes

# Create inventory
def createInventory():
    print '\nTASK: Create Inventory ***\n'
    print '** Connecting to the cloud **\n'

    # Get Cloud
    driver = cls(USER, API_KEY, region='iad')

    print '** Gathering the cloud information **\n'

    # Get node list
    nodes = driver.list_nodes()
    
    print '** Creating inventory file', inventoryFilename, '**\n'
    
    for node in nodes:
        if 'loadbalancer' in node.name:
            lbip = node.extra['access_ip']
            
        elif 'drupal-01' in node.name:
            d1ip = node.private_ips[0]
            
        elif 'drupal-02' in node.name:
            d2ip = node.private_ips[0]
            
        elif 'nfs-01' in node.name:
            n1ip = node.private_ips[0]
            
        elif 'nfs-02' in node.name:
            n2ip = node.private_ips[0]
            
        elif 'mysql-01' in node.name:
            m1ip = node.private_ips[0]
            
        elif 'mysql-02' in node.name:
            m2ip = node.private_ips[0]
    
    # Write to file
    fo = open(inventoryFilename, 'w+')
    
    fo.write('127.0.0.1\n\n');
    fo.write('[loadbalancer]\n');
    fo.write('lb1 ansible_ssh_host=%s primary=%s ansible_ssh_user=%s\n\n' % (lbip, 'yes', SSH_USERNAME))
    fo.write('[drupal]\n');
    fo.write('drupal1 ansible_ssh_host=%s primary=%s ansible_ssh_user=%s\n' % (d1ip, 'yes', SSH_USERNAME))
    fo.write('drupal2 ansible_ssh_host=%s primary=%s ansible_ssh_user=%s\n\n' % (d2ip, 'no', SSH_USERNAME))
    fo.write('[nfs]\n');
    fo.write('nfs1 ansible_ssh_host=%s primary=%s ansible_ssh_user=%s\n' % (n1ip, 'yes', SSH_USERNAME))
    fo.write('nfs2 ansible_ssh_host=%s primary=%s ansible_ssh_user=%s\n\n' % (n2ip, 'no', SSH_USERNAME))
    fo.write('[mysql]\n');
    fo.write('mysql1 ansible_ssh_host=%s primary=%s ansible_ssh_user=%s\n' % (m1ip, 'yes', SSH_USERNAME))
    fo.write('mysql2 ansible_ssh_host=%s primary=%s ansible_ssh_user=%s' % (m2ip, 'no', SSH_USERNAME))
    
    fo.close()
    
    print ('127.0.0.1\n');
    print ('[loadbalancer]');
    print ('lb1 ansible_ssh_host=%s primary=%s ansible_ssh_user=root\n' % (lbip, 'yes', SSH_USERNAME))
    print ('[drupal]\n');
    print ('drupal1 ansible_ssh_host=%s primary=%s ansible_ssh_user=%s' % (d1ip, 'yes', SSH_USERNAME))
    print ('drupal2 ansible_ssh_host=%s primary=%s ansible_ssh_user=%s\n' % (d2ip, 'no', SSH_USERNAME))
    print ('[nfs]\n');
    print ('nfs1 ansible_ssh_host=%s primary=%s ansible_ssh_user=%s' % (n1ip, 'yes', SSH_USERNAME))
    print ('nfs2 ansible_ssh_host=%s primary=%s ansible_ssh_user=%s\n' % (n2ip, 'no', SSH_USERNAME))
    print ('[mysql]\n');
    print ('mysql1 ansible_ssh_host=%s primary=%s ansible_ssh_user=%s' % (m1ip, 'yes', SSH_USERNAME))
    print ('mysql2 ansible_ssh_host=%s primary=%s ansible_ssh_user=%s' % (m2ip, 'no', SSH_USERNAME))
    print ''
    
    return
# Create inventory

print 'Rackspace console (for Python 2.7.6)'

while (1):
    print ''
    print '1: Create nodes'
    print '2: Create volumes'
    print '3: List nodes'
    print '4: List volumes'
    print '5: Attach volumes'
    print '6: Create inventory'
    print '9: Create All'
    print '0: Exit'
    
    uinp = raw_input('> ')
    
    # Exit
    if uinp in ('0', 'exit'):
        print 'Goodbye'
        exit()
    
    # Create nodes
    elif uinp == '1':
        createNodes()
    
    # Create volumes
    elif uinp == '2': 
        createVolumes()
    
    # List nodes
    elif uinp == '3': 
        listNodes()
        
    # List volumes
    elif uinp == '4': 
        listVolumes()
        
    # Attach volumes
    elif uinp == '5':
        attachVolumes()
        
    # Create inventory
    elif uinp == '6':
        createInventory()
        
    # Create all
    elif uinp == '9':
        print '\nThis will create volumes, nodes, attach volumes and write the inventory file. Are you sure you want to continue? (y/n)'
        uinp = raw_input('> ')
        
        if uinp in ('y', 'Y'):
            createVolumes()
            createNodes()
            attachVolumes()
            createInventory()
