(() => {
  const provider = document.getElementById('provider');
  const lifeFields = document.getElementById('life-fields');
  const healthFields = document.getElementById('health-fields');
  const lifeRequirement = document.getElementById('life_requirement');
  const lifeAge = document.getElementById('life_age');
  const familyType = document.getElementById('family_type');
  const membersContainer = document.getElementById('members-container');
  const existingInsurance = document.getElementById('existing_insurance');

  function setRequired(el, required) { if (el) el.required = required; }
  function updateProviderFields() {
    const isLife = provider.value === 'Tata AIA Life Insurance' || provider.value === 'LIC';
    const isHealth = provider.value === 'Care Health Insurance';
    lifeFields.hidden = !isLife;
    healthFields.hidden = !isHealth;
    setRequired(lifeRequirement, isLife);
    setRequired(lifeAge, isLife);
    setRequired(familyType, isHealth);
    setRequired(existingInsurance, isHealth);
    membersContainer.querySelectorAll('input,select').forEach(el => el.required = isHealth && !!familyType.value);
  }
  function createMemberField(index, label, relationshipOptions, defaultRelationship) {
    const card = document.createElement('div');
    card.className = 'member-card';
    const heading = document.createElement('h4');
    heading.textContent = label;
    card.appendChild(heading);
    const nameLabel = document.createElement('label');
    nameLabel.textContent = 'Full name *';
    const name = document.createElement('input'); name.name = `member_${index}_name`; name.maxLength = 100; name.placeholder = 'Member full name'; name.required = true;
    nameLabel.appendChild(name); card.appendChild(nameLabel);
    const ageLabel = document.createElement('label'); ageLabel.textContent = 'Age or date of birth *';
    const age = document.createElement('input'); age.name = `member_${index}_age`; age.maxLength = 40; age.placeholder = 'e.g. 35 years'; age.required = true;
    ageLabel.appendChild(age); card.appendChild(ageLabel);
    const relLabel = document.createElement('label'); relLabel.textContent = 'Relationship *';
    const rel = document.createElement('select'); rel.name = `member_${index}_relationship`; rel.required = true;
    relationshipOptions.forEach(value => { const opt = document.createElement('option'); opt.value = value; opt.textContent = value; if (value === defaultRelationship) opt.selected = true; rel.appendChild(opt); });
    relLabel.appendChild(rel); card.appendChild(relLabel);
    const genderLabel = document.createElement('label'); genderLabel.textContent = 'Gender (optional)';
    const gender = document.createElement('select'); gender.name = `member_${index}_gender`;
    ['', 'Female', 'Male', 'Other', 'Prefer not to say'].forEach(value => { const opt = document.createElement('option'); opt.value = value; opt.textContent = value || 'Select'; gender.appendChild(opt); });
    genderLabel.appendChild(gender); card.appendChild(genderLabel);
    return card;
  }
  function updateMembers() {
    membersContainer.replaceChildren();
    if (!familyType.value) { updateProviderFields(); return; }
    const options = familyType.value === '2 Adults + 2 Children'
      ? [['Adult 1', ['Self', 'Spouse', 'Parent', 'Other adult'], 'Self'], ['Adult 2', ['Spouse', 'Parent', 'Other adult', 'Self'], 'Spouse'], ['Child 1', ['Child', 'Son', 'Daughter'], 'Child'], ['Child 2', ['Child', 'Son', 'Daughter'], 'Child']]
      : [['Adult 1', ['Self', 'Spouse', 'Parent', 'Sibling', 'Other adult'], 'Self'], ['Adult 2', ['Spouse', 'Parent', 'Sibling', 'Other adult', 'Self'], 'Spouse'], ['Adult 3', ['Parent', 'Parent-in-law', 'Sibling', 'Other adult'], 'Parent'], ['Adult 4', ['Parent', 'Parent-in-law', 'Sibling', 'Other adult'], 'Parent']];
    options.forEach((item, idx) => membersContainer.appendChild(createMemberField(idx + 1, item[0], item[1], item[2])));
    updateProviderFields();
  }
  if (provider) provider.addEventListener('change', updateProviderFields);
  if (familyType) familyType.addEventListener('change', updateMembers);
  document.querySelectorAll('[data-select-provider]').forEach(link => link.addEventListener('click', () => {
    if (provider) { provider.value = link.dataset.selectProvider; updateProviderFields(); }
  }));
  updateProviderFields();
})();
