// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TenderContract {

    struct Bid {
        string dKey;
        string checksum;
    }

    uint256[] private tenderIds;
    mapping (uint256 => uint256) private startTime;
    mapping (uint256 => uint256) private endTime;
    mapping (uint256 => mapping(uint256 => Bid)) private bid;
    mapping (uint256 => uint256[]) private bidderIds;

    event BidderKeyRetrieved(uint256 tenderId, uint256 bidderId, string externalChecksum, string dKey);
    event TenderKeysRetrieved(uint256 tenderId, uint256[] bidderIds, string[] externalChecksums, string[] dKeys);
    event TenderCreated(uint256 tenderId, uint256 createdTime, uint256 startTime, uint256 endTime);
    event BidAdded(uint256 tenderId, uint256 bidderId);

    function tenderIsPresent(uint256 _tenderId) private view returns (bool) {
        for (uint256 i = 0; i < tenderIds.length; i++) if( _tenderId == tenderIds[i] ) return true;
        return false;
    }

    function bidderForTenderIsPresent(uint256 _tenderId, uint256 _bidderId) private view returns (bool) {
        for (uint256 i = 0; i < bidderIds[_tenderId].length; i++) if( _bidderId == bidderIds[_tenderId][i]) return true;
        return false;
    }

    function createTender(uint256 _tenderId, uint256 _startTime, uint256 _endTime) external {
        require(!tenderIsPresent(_tenderId), "Tender already exists");
        require(block.timestamp < _startTime, "Invalid Start Time");
        require(block.timestamp < _endTime, "Invalid End Time");
        tenderIds.push(_tenderId);
        startTime[_tenderId] = _startTime;
        endTime[_tenderId] = _endTime;
        emit TenderCreated(_tenderId, block.timestamp, _startTime, _endTime);
    }

    function placeBid(uint256 _tenderId, uint256 _bidderId, string calldata _dKey, string calldata _checksum) external {
        require(tenderIsPresent(_tenderId), "Invalid Tender ID");
        require(!bidderForTenderIsPresent(_tenderId, _bidderId), "Bid already exists");
        require(block.timestamp > startTime[_tenderId], "Tender is not started");
        require(block.timestamp < endTime[_tenderId], "Tender has ended");
        bidderIds[_tenderId].push(_bidderId);
        bid[_tenderId][_bidderId] = Bid(_dKey, _checksum);
        emit BidAdded(_tenderId, _bidderId);
    }

    function retrieveDKey(uint256 _tenderId, uint256 _bidderId, string calldata _checksum) external {
        require(tenderIsPresent(_tenderId), "Invalid Tender ID");
        require(bidderForTenderIsPresent(_tenderId, _bidderId), "Invalid Bidder ID");
        require(block.timestamp >= startTime[_tenderId], "Tender is not started");
        require(block.timestamp >= endTime[_tenderId], "Tender is still active");
        require(keccak256(abi.encodePacked(_checksum)) == keccak256(abi.encodePacked(bid[_tenderId][_bidderId].checksum)), "Invalid checksum");
        string memory dKey = bid[_tenderId][_bidderId].dKey;
        emit BidderKeyRetrieved(_tenderId, _bidderId, _checksum, dKey);
    }

    function retrieveDKeysForTender(uint256 _tenderId, uint256[] calldata _bidderIds, string[] calldata _checksums) external {
        require(tenderIsPresent(_tenderId), "Invalid Tender ID");
        require(block.timestamp >= startTime[_tenderId], "Tender is not started");
        require(block.timestamp >= endTime[_tenderId], "Tender is still active");
        require(_bidderIds.length == _checksums.length, "Arrays length mismatch");
        string[] memory decryptionKeys = new string[](_bidderIds.length);
        for (uint256 i = 0; i < _bidderIds.length; i++) {
            uint256 _bidderId = _bidderIds[i];
            string memory storedChecksum = bid[_tenderId][_bidderId].checksum;
            if (bidderForTenderIsPresent(_tenderId, _bidderId) && keccak256(abi.encodePacked(_checksums[i])) == keccak256(abi.encodePacked(storedChecksum))) {
                decryptionKeys[i] = bid[_tenderId][_bidderId].dKey;
            } else { decryptionKeys[i] = ""; }
        }
        emit TenderKeysRetrieved(_tenderId, _bidderIds, _checksums, decryptionKeys);
    }
}