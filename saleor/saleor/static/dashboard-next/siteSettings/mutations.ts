import gql from "graphql-tag";

import { TypedMutation } from "../mutations";
import { fragmentAddress } from "../orders/queries";
import { shopFragment } from "./queries";
import {
  AuthorizationKeyAdd,
  AuthorizationKeyAddVariables
} from "./types/AuthorizationKeyAdd";
import {
  AuthorizationKeyDelete,
  AuthorizationKeyDeleteVariables
} from "./types/AuthorizationKeyDelete";
import {
  ShopSettingsUpdate,
  ShopSettingsUpdateVariables
} from "./types/ShopSettingsUpdate";

const authorizationKeyAdd = gql`
  ${shopFragment}
  mutation AuthorizationKeyAdd(
    $input: AuthorizationKeyInput!
    $keyType: AuthorizationKeyType!
  ) {
    authorizationKeyAdd(input: $input, keyType: $keyType) {
      errors {
        field
        message
      }
      shop {
        ...ShopFragment
      }
    }
  }
`;
export const TypedAuthorizationKeyAdd = TypedMutation<
  AuthorizationKeyAdd,
  AuthorizationKeyAddVariables
>(authorizationKeyAdd);

const authorizationKeyDelete = gql`
  ${shopFragment}
  mutation AuthorizationKeyDelete($keyType: AuthorizationKeyType!) {
    authorizationKeyDelete(keyType: $keyType) {
      errors {
        field
        message
      }
      shop {
        ...ShopFragment
      }
    }
  }
`;
export const TypedAuthorizationKeyDelete = TypedMutation<
  AuthorizationKeyDelete,
  AuthorizationKeyDeleteVariables
>(authorizationKeyDelete);

const shopSettingsUpdate = gql`
  ${shopFragment}
  ${fragmentAddress}
  mutation ShopSettingsUpdate(
    $shopDomainInput: SiteDomainInput!
    $shopSettingsInput: ShopSettingsInput!
    $addressInput: AddressInput!
  ) {
    shopSettingsUpdate(input: $shopSettingsInput) {
      errors {
        field
        message
      }
      shop {
        ...ShopFragment
      }
    }
    shopDomainUpdate(input: $shopDomainInput) {
      errors {
        field
        message
      }
      shop {
        domain {
          host
          url
        }
      }
    }
    shopAddressUpdate(input: $addressInput) {
      errors {
        field
        message
      }
      shop {
        companyAddress {
          ...AddressFragment
        }
      }
    }
  }
`;
export const TypedShopSettingsUpdate = TypedMutation<
  ShopSettingsUpdate,
  ShopSettingsUpdateVariables
>(shopSettingsUpdate);
