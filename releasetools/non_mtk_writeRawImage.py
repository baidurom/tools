#!/usr/bin/env python

import common

def WriteRawImage(self, mount_point, fn):
    print ">>> in non_mtk_writeRawImage.py, fn:%s, mount_point:%s" %(fn, mount_point)

    edifyGenerator = self.script
    fstab = edifyGenerator.info["fstab"]
    if fstab:
      p = fstab[mount_point]
      partition_type = common.PARTITION_TYPES[p.fs_type]
      args = {'device': p.device, 'fn': fn}
      if partition_type == "MTD":
        edifyGenerator.script.append(
            'write_raw_image(package_extract_file("%(fn)s"), "%(device)s");'
            % args)
      elif partition_type == "EMMC":
        edifyGenerator.script.append(
              'package_extract_file("%(fn)s", "%(device)s");' % args)
      else:
        raise ValueError("don't know how to write \"%s\" partitions" % (p.fs_type,))

    return True

