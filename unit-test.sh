coverage run --source IM_Backend,UserManage,FriendRelation -m pytest --junit-xml=xunit-reports/xunit-result.xml
ret=$?
coverage xml -o coverage-reports/coverage.xml
coverage report
exit $ret