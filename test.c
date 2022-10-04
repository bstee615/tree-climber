sparse_scan_file (struct tar_sparse_file *file)
{
  /* always check for completely sparse files */
  if (sparse_scan_file_wholesparse (file))
    return true;

  switch (hole_detection)
    {
    case HOLE_DETECTION_DEFAULT:
    case HOLE_DETECTION_SEEK:
#ifdef SEEK_HOLE
      if (sparse_scan_file_seek (file))
        return true;
#else
      if (hole_detection == HOLE_DETECTION_SEEK)
	WARN((0, 0,
	      _("\"seek\" hole detection is not supported, using \"raw\".")));
      /* fall back to "raw" for this and all other files */
      hole_detection = HOLE_DETECTION_RAW;
#endif
      FALLTHROUGH;
    case HOLE_DETECTION_RAW:
      if (sparse_scan_file_raw (file))
	return true;
    }

  return false;
}

