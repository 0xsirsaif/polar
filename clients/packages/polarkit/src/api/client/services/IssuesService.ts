/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { IssueSchema } from '../models/IssueSchema';
import type { Platforms } from '../models/Platforms';

import type { CancelablePromise } from '../core/CancelablePromise';
import type { BaseHttpRequest } from '../core/BaseHttpRequest';

export class IssuesService {

  constructor(public readonly httpRequest: BaseHttpRequest) {}

  /**
   * Get Repository Issues
   * @returns IssueSchema Successful Response
   * @throws ApiError
   */
  public getRepositoryIssues({
    platform,
    organizationName,
    name,
  }: {
    platform: Platforms,
    organizationName: string,
    name: string,
  }): CancelablePromise<Array<IssueSchema>> {
    return this.httpRequest.request({
      method: 'GET',
      url: '/api/v1/issues/{platform}/{organization_name}/{name}',
      path: {
        'platform': platform,
        'organization_name': organizationName,
        'name': name,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }

}