PRINTED = ['Tower', 'HousingBox', 'Crank', 'Rod', 'OuterKnuckle_L', 'OuterKnuckle_R', 'OuterFinger', 'InnerKnuckle',
           'InnerFinger', 'Fingertip', 'SpacerA', 'SpacerB', 'CameraMount']


def export_parts(raw_dir):
    """Main body of every printed component, in component space (= assembly space at q = 0 for left parts)."""
    em = des.exportManager
    tb = adsk.fusion.TemporaryBRepManager.get()
    out = []
    for n in PRINTED:
        comp, occ = get_comp(n, create=False)
        b = main_body(comp, n)
        o = em.createSTLExportOptions(b, raw_dir + '/' + n + '.stl')
        o.isBinaryFormat = True
        o.unitType = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        o.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        o.sendToPrintUtility = False
        em.execute(o)
        out.append(n)
    return out


def export_assembly(step_path, f3d_path):
    em = des.exportManager
    em.execute(em.createSTEPExportOptions(step_path, root))
    em.execute(em.createFusionArchiveExportOptions(f3d_path, root))
    return 'ok'
