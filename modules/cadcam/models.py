from django.db import models


class CADProject(models.Model):
    STATUS = [('active', 'Active'), ('archived', 'Archived'), ('pending_integration', 'Pending Integration')]
    TOOLS = [
        ('fusion360', 'Autodesk Fusion 360'),
        ('freecad', 'FreeCAD'),
        ('camotics', 'CAMotics (Simulation)'),
        ('other', 'Other'),
    ]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='cadcam_projects')
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    tool = models.CharField(max_length=30, choices=TOOLS, default='other')
    status = models.CharField(max_length=30, choices=STATUS, default='pending_integration')
    owner = models.ForeignKey('bredbound.BusinessEmployee', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.name


class CADFile(models.Model):
    FORMATS = [
        ('step', 'STEP (.step/.stp)'), ('iges', 'IGES (.iges/.igs)'),
        ('stl', 'STL (.stl)'), ('dxf', 'DXF (.dxf)'),
        ('dwg', 'DWG (.dwg)'), ('f3d', 'Fusion 360 (.f3d)'),
        ('fcstd', 'FreeCAD (.FCStd)'), ('gcode', 'G-code (.nc/.gcode)'),
        ('other', 'Other'),
    ]
    project = models.ForeignKey(CADProject, on_delete=models.CASCADE, related_name='files')
    filename = models.CharField(max_length=200)
    file = models.FileField(upload_to='cadcam/files/', null=True, blank=True)
    format = models.CharField(max_length=10, choices=FORMATS, default='other')
    version = models.CharField(max_length=20, default='1.0')
    description = models.CharField(max_length=200, blank=True)
    uploaded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.filename} ({self.format})"
