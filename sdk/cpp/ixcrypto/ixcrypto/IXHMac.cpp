/*
 *  IXHMac.h
 *  Author: Benjamin Sergeant
 *  Copyright (c) 2018 Machine Zone. All rights reserved.
 */

#include "IXHMac.h"

#include "IXBase64.h"

#if defined(__APPLE__)
#include <CommonCrypto/CommonHMAC.h>
#else
#include <mbedtls/md.h>
#endif

namespace ix
{
    std::string hmac(const std::string& data, const std::string& key)
    {
        constexpr size_t hashSize = 16;
        unsigned char hash[hashSize];

#if defined(__APPLE__)
        CCHmac(kCCHmacAlgMD5, key.c_str(), key.size(), data.c_str(), data.size(), &hash);
#else
        mbedtls_md_hmac(mbedtls_md_info_from_type(MBEDTLS_MD_MD5),
                        (unsigned char*) key.c_str(),
                        key.size(),
                        (unsigned char*) data.c_str(),
                        data.size(),
                        (unsigned char*) &hash);
#endif

        std::string hashString(reinterpret_cast<char*>(hash), hashSize);

        return base64_encode(hashString, (uint32_t) hashString.size());
    }
} // namespace ix
