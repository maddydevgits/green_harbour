const demo=artifacts.require('TokenManagementSystem')
module.exports=function(deployer){
    deployer.deploy(demo)
}