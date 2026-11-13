! Stub of FMS's check_nml_error for a standalone build of gfdl_mp.F90
module fms_mod
  implicit none
contains
  integer function check_nml_error(ios, name)
    integer, intent(in) :: ios
    character(len=*), intent(in) :: name
    check_nml_error = ios
    if (ios > 0) print *, 'namelist error in ', name, ios
  end function check_nml_error
end module fms_mod
