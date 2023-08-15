/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AccountType } from './AccountType';
import type { CurrencyAmount } from './CurrencyAmount';
import type { Issue } from './Issue';
import type { Pledger } from './Pledger';
import type { PledgeState } from './PledgeState';

export type BackofficePledge = {
  /**
   * Pledge ID
   */
  id: string;
  /**
   * When the pledge was created
   */
  created_at: string;
  /**
   * Amount pledged towards the issue
   */
  amount: CurrencyAmount;
  /**
   * Current state of the pledge
   */
  state: PledgeState;
  /**
   * If and when the pledge was refunded to the pledger
   */
  refunded_at?: string;
  /**
   * When the payout is scheduled to be made to the maintainers behind the issue. Disputes must be made before this date.
   */
  scheduled_payout_at?: string;
  /**
   * The issue that the pledge was made towards
   */
  issue: Issue;
  /**
   * The user or organization that made this pledge
   */
  pledger?: Pledger;
  payment_id?: string;
  dispute_reason?: string;
  disputed_by_user_id?: string;
  disputed_at?: string;
  pledger_email?: string;
  to_organization_account_type?: AccountType;
};
