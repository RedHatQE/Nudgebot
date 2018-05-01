angular
    .module('dashboard', ['ngMaterial'])
    .controller('tabController', tabController);

function tabController ($scope) {            
    $scope.data = {
      selectedIndex: 0,
      secondLocked:  true,
      secondLabel:   "2",
      bottom:        false
    };

    $scope.next = function() {
        $scope.data.selectedIndex = Math.min($scope.data.selectedIndex + 1, 2) ;
    };

    $scope.previous = function() {
        $scope.data.selectedIndex = Math.max($scope.data.selectedIndex - 1, 0);
    };
}
