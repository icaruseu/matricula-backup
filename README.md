# Matricula Backup

This is a Python script intended to back up image folders on the Matricula Image
server to AWS S3 with the Deep Archive storage class.

## Todo

- [ ] Fix non-unicode file names, for instance
      `'ABP_AdminA_Alt'$'\366''tting_AR_108-0010v.jpg'`
- [ ] Check how the images are linked on matricula and define a prefix (or
      something similar) that makes the paths in the s3 buckets work with
      matricula directly. Check if this could work at all, do the archives all
      have their individual image server configuration?
