// SPDX-License-Identifier: MIT
pragma solidity >=0.4.22 <0.9.0;

contract TokenManagementSystem {
  
  uint[] _phoneno;
  uint[] _tokens;

  uint[] _entryids;
  uint[] _binweight;
  uint[] _itokens;
  uint[] _iphoneno;

  mapping(uint=>bool) _registeredentries;
  mapping(uint=>bool) _registeredUsers;

  function addTransaction(uint entryid,uint binweight,uint itoken,uint iphoneno) public {
    require(!_registeredentries[entryid]);

    _entryids.push(entryid);
    _binweight.push(binweight);
    _itokens.push(itoken);
    _iphoneno.push(iphoneno);

    updateBalance(iphoneno, itoken);

    _registeredentries[entryid]=true;
  }

  function viewTransactions() public view returns(uint[] memory,uint[] memory, uint[] memory, uint[] memory){
    return (_entryids,_binweight,_itokens,_iphoneno);
  }

  function updateBalance(uint iphoneno,uint newtokens) public {
    uint i;
    for(i=0;i<_phoneno.length;i++){
      if(_phoneno[i]==iphoneno){
        _tokens[i]+=newtokens;
      }
    }
  }

  function addToken(uint phoneno,uint token) public {
    require(!_registeredUsers[phoneno]);
    _phoneno.push(phoneno);
    _tokens.push(token);
    _registeredUsers[phoneno]=true;
  }

  function updateToken(uint phoneno,uint token) public {
    uint i;
    for(i=0;i<_phoneno.length;i++){
      if(phoneno==_phoneno[i]){
        _tokens[i]=token;
      }
    }
  }

  function viewTokens() public view returns (uint[] memory,uint[] memory) {
    return(_phoneno,_tokens);
  }

  function transferToken(uint from,uint to, uint token) public {
    uint i;
    for(i=0;i<_phoneno.length;i++) {
      if(from==_phoneno[i]) {
        _tokens[i]-=token;
      }
      if(to==_phoneno[i]){
        _tokens[i]+=token;
      }
    }
  }

}
