from flask import Blueprint, request, jsonify, abort, make_response

from sherlockapi import db, auth
from sherlockapi.data.model import (Case, TestCaseSchema, StateType,
                                    CycleCases, TagCase)
from sherlockapi.helpers.string_operations import check_none_and_blank
from sherlockapi.helpers.util import (get_scenario, get_tstcase,
                                      get_last_cycle, get_tagcase)


test_case = Blueprint('test_cases', __name__)


@test_case.route('/register_tag', methods=['POST'])
@auth.login_required
def register_tag(scenario_id):
    """POST endpoint for adding a tag to a case.

    Param:
        {
        'case_id': required,
        'tag': required
        }
    """
    scenario = get_scenario(scenario_id)
    case_id = check_none_and_blank(request, 'case_id')
    case = get_tstcase(case_id)
    tag = check_none_and_blank(request, 'tag')
    new_tag = TagCase(case_id=case_id,
                      tag=tag)
    db.session.add(new_tag)
    db.session.commit()

    return make_response(jsonify(message='TAG_CREATED'))


@test_case.route('/remove_tag', methods=['POST'])
@auth.login_required
def remove_tag(scenario_id):
    scenario = get_scenario(scenario_id)
    case_id = check_none_and_blank(request, 'case_id')
    case = get_tstcase(case_id)
    tag_id = check_none_and_blank(request, 'tag_id')
    tag = get_tagcase(tag_id)
    db.session.delete(tag)
    db.session.commit()
    return make_response(jsonify(message='TAG_REMOVED'))


@test_case.route('/show/<int:test_case_id>', methods=['GET'])
@auth.login_required
def show_testcase(scenario_id, test_case_id):
    """Return Testcase Info."""
    tst_case = get_tstcase(test_case_id)
    tstcase_schema = TestCaseSchema(many=False)
    tstcase = tstcase_schema.dump(tst_case).data
    return make_response(jsonify(tstcase))


@test_case.route('/new', methods=['POST'])
@auth.login_required
def new(scenario_id):
    """POST endpoint for new scenarios.

    Param:
        {'case_name': required }
    """
    case_name = check_none_and_blank(request, 'case_name')

    scenario = get_scenario(scenario_id)
    case = Case(name=case_name, scenario_id=scenario.id)
    db.session.add(case)
    db.session.commit()

    project_lasty_cycle = get_last_cycle(scenario.project_id)

    if project_lasty_cycle:
        cyclecase = CycleCases(cycle_id=project_lasty_cycle.id,
                               case_id=case.id,
                               scenario_id=case.scenario_id)
        db.session.add(cyclecase)
        db.session.commit()

    return make_response(jsonify(message='CASE_CREATED'))


@test_case.route('/change_status', methods=['POST'])
@auth.login_required
def tstcase_changestatus(scenario_id):
    """POST endpoint for new scenarios.

    Param:
        {
         'case_id': required,
         'action': required,
        }

    TODO: State is not defined
    """

    case_id = check_none_and_blank(request, 'case_id')
    action = check_none_and_blank(request, 'action')
    scenario = get_scenario(scenario_id)
    tst_case = get_tstcase(case_id)

    if scenario.state_code == StateType.disable:
        return make_response(jsonify(message='SCENARIO_DISABLED'))

    last_cycle = get_last_cycle(scenario.project_id)

    if last_cycle:
        cycle_case = CycleCases.query.filter_by(
            cycle_id=last_cycle.id).filter_by(case_id=case_id).first()

    if action == 'DISABLE':
        state = StateType.disable
        cycle_state = StateType.blocked
    elif action == 'ENABLE':
        state = StateType.active
        cycle_state = StateType.not_executed
    elif action == 'REMOVE':
        if last_cycle and last_cycle.state_code == StateType.active:
            cycle_state = None
            if cycle_case:
                db.session.delete(cycle_case)
                db.session.commit()
        state = StateType.removed
    else:
        return make_response(jsonify(message='ACTION_UNKNOW'))

    tst_case.state_code = state
    db.session.add(tst_case)
    db.session.commit()

    if last_cycle:
        if last_cycle.state_code == StateType.active:
            if cycle_case and cycle_state:
                cycle_case.state_code = cycle_state
                db.session.add(cycle_case)
                db.session.commit()

    return make_response(jsonify(message='DONE'))


@test_case.route('/edit', methods=['POST'])
@auth.login_required
def edit(scenario_id):
    """POST endpoint for edit scenarios.

    Param:
        {
         'case_name': required,
         'case_id': required
        }
    """
    case_id = check_none_and_blank(request, 'case_id')
    new_case_name = check_none_and_blank(request, 'case_name')

    edited_tc = get_tstcase(case_id)

    edited_tc.name = new_case_name
    db.session.add(edited_tc)
    db.session.commit()

    return make_response(jsonify(message='CASE_EDITED'))
